import json
import logging
from contextlib import asynccontextmanager
from datetime import timezone
from io import BytesIO

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import llm
from .auth import create_token, get_current_user, hash_password, verify_password
from .config import settings
from .db import Base, Scan, SessionLocal, User, engine, get_db
from .detector import Detector
from .grading import analyse
from .weather import get_weather
from .weather import last_error as weather_errors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("fasalscan")

LANGS = {"en", "ur", "ps"}
state: dict = {"detector": None}


def _seed_demo_user() -> None:
    with SessionLocal() as db:
        exists = db.scalar(select(User).where(User.email == settings.DEMO_EMAIL))
        if not exists:
            db.add(User(
                email=settings.DEMO_EMAIL,
                name=settings.DEMO_NAME,
                password_hash=hash_password(settings.DEMO_PASSWORD),
            ))
            db.commit()
            log.info("Seeded demo user %s", settings.DEMO_EMAIL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    _seed_demo_user()
    state["detector"] = Detector(settings.MODEL_PATH)
    yield


app = FastAPI(title="FasalScan API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- schemas ----------
class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lang: str = "en"
    scan_id: int | None = None


def _user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name}


def _scan_out(s: Scan) -> dict:
    report = json.loads(s.report_json or "{}")
    created = s.created_at if s.created_at.tzinfo else s.created_at.replace(tzinfo=timezone.utc)
    return {
        "id": s.id,
        "created_at": created.isoformat(),
        "lang": s.lang,
        "summary": s.summary,
        **report,
    }


def _lang(value: str) -> str:
    return value if value in LANGS else "en"


# ---------- routes ----------
@app.get("/")
def root():
    return {"app": settings.APP_NAME, "docs": "/docs", "health": "/api/health"}


@app.get("/api/health")
async def health(deep: bool = False):
    det = state["detector"]
    out = {
        "status": "ok",
        "model_loaded": bool(det and det.available),
        "classes": list(det.names.values()) if det and det.available else [],
        "llm_enabled": bool(settings.GROQ_API_KEY),
    }
    if deep:  # live checks of the outside services, no secrets returned
        w = await get_weather(settings.DEFAULT_LAT, settings.DEFAULT_LON)
        out["weather"] = {"source": w["source"], "error": weather_errors["weather"]}
        out["llm"] = await llm.llm_status()
    return out


@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password.")
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": _user_out(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


MAX_IMAGES_PER_SCAN = 12


def _load_image(data: bytes, n: int) -> Image.Image:
    if not data:
        raise HTTPException(400, f"Photo {n} is empty.")
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Photo {n} is larger than {settings.MAX_UPLOAD_MB:g} MB.")
    try:
        img = Image.open(BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, f"Photo {n} doesn't look like an image.")
    img.thumbnail((settings.MAX_IMAGE_SIDE, settings.MAX_IMAGE_SIDE))
    return img


def _predict_all(det: Detector, imgs: list[Image.Image]) -> tuple[list[dict], list[int]]:
    detections, per_image = [], []
    for i, img in enumerate(imgs):
        found = det.predict(img)
        for d in found:
            d["image"] = i
        detections.extend(found)
        per_image.append(len(found))
    return detections, per_image


@app.post("/api/scan")
async def scan(
    images: list[UploadFile] | None = File(None),
    image: UploadFile | None = File(None),
    lang: str = Form("en"),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """One or more photos of the same lot. Several close-up photos of fruit picked at
    random from a crate give a fairer grade than one wide shot (that's how inspectors sample)."""
    det: Detector | None = state["detector"]
    if det is None or not det.available:
        raise HTTPException(503, "The vision model isn't loaded on the server yet.")

    uploads = [u for u in (images or []) if u is not None] + ([image] if image else [])
    if not uploads:
        raise HTTPException(400, "Add at least one photo.")
    if len(uploads) > MAX_IMAGES_PER_SCAN:
        raise HTTPException(400, f"Up to {MAX_IMAGES_PER_SCAN} photos per scan.")
    imgs = [_load_image(await u.read(), n) for n, u in enumerate(uploads, 1)]

    lang = _lang(lang)
    lat = lat if lat is not None and -90 <= lat <= 90 else settings.DEFAULT_LAT
    lon = lon if lon is not None and -180 <= lon <= 180 else settings.DEFAULT_LON

    detections, per_image = await run_in_threadpool(_predict_all, det, imgs)
    weather = await get_weather(lat, lon)
    report = analyse(detections, weather)
    report["weather"] = weather
    report["photos"] = len(imgs)
    report["per_photo"] = per_image
    summary = await llm.summarise(report, weather, lang)

    row = Scan(
        user_id=user.id,
        lang=lang,
        fruit=report["fruit"],
        grade=report["grade"],
        total=report["total"],
        rotten=report["rotten"],
        reject_pct=report["reject_pct"],
        days_left=report["days_left"],
        summary=summary,
        report_json=json.dumps(report, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _scan_out(row)


@app.get("/api/scans")
def list_scans(limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    rows = db.scalars(
        select(Scan).where(Scan.user_id == user.id).order_by(Scan.created_at.desc()).limit(limit)
    ).all()
    out = []
    for s in rows:
        item = _scan_out(s)
        item.pop("detections", None)  # keep the list light
        out.append(item)
    return out


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(Scan, scan_id)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Scan not found.")
    return _scan_out(s)


@app.post("/api/ask")
async def ask(body: AskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.scan_id is not None:
        s = db.get(Scan, body.scan_id)
        if not s or s.user_id != user.id:
            raise HTTPException(404, "Scan not found.")
    else:
        s = db.scalar(select(Scan).where(Scan.user_id == user.id).order_by(Scan.created_at.desc()).limit(1))

    report = json.loads(s.report_json) if s else None
    weather = report.get("weather") if report else None
    answer, from_llm = await llm.ask(body.question.strip(), report, weather, _lang(body.lang))
    return {"answer": answer, "scan_id": s.id if s else None, "ai": from_llm}


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    lang: str = Form("ur"),
    user: User = Depends(get_current_user),
):
    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty recording.")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Recording too long.")
    try:
        text = await llm.transcribe(data, audio.filename or "speech.webm", audio.content_type, _lang(lang))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
    except httpx.HTTPError as exc:
        log.warning("Transcription failed: %s", exc)
        raise HTTPException(502, "Couldn't understand the recording, please try again.")
    if not text:
        raise HTTPException(422, "Didn't catch anything, try speaking a bit closer to the mic.")
    return {"text": text}
