# FasalScan

Photograph a crate of fruit, get a grade, the share that's damaged, and an estimate of how many days it has before quality drops. Answers in English, Urdu or Pashto, by text or voice.

**Live demo:** _add your Vercel link here_ · Demo login: `demo@fasalscan.app` / `demo1234`

## How it works

1. The phone resizes the photo and uploads it.
2. A YOLOv8n model (ONNX Runtime, CPU) finds every fruit and labels it fresh or rotten.
3. A grading step turns counts into a grade (A ≤5% damaged, B ≤15%, C ≤35%, D above).
4. Shelf life is estimated from fruit type, damage share and the next few days of temperature from Open-Meteo (Q10 ≈ 2 rule of thumb).
5. An open-weight LLM (Llama 3.3 70B, served via Groq) writes a short plain-language summary and answers follow-up questions. Whisper handles voice. Without an API key, built-in English/Urdu templates take over so the app never breaks.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite, plain CSS, mobile-first |
| API | FastAPI, SQLAlchemy 2, JWT (PyJWT + bcrypt) |
| Vision | YOLOv8n → ONNX, NumPy letterbox + NMS (no OpenCV) |
| Language | Llama 3.3 70B + Whisper large-v3-turbo via Groq's OpenAI-compatible API |
| Data | SQLite locally, PostgreSQL in production |
| Hosting | Vercel (web), Render (API) |

## Run locally

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp /path/to/best.onnx models/best.onnx
export GROQ_API_KEY=gsk_...        # optional
uvicorn app.main:app --reload       # http://localhost:8000/docs

# frontend (new terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev                         # http://localhost:5173
```

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | email + password → JWT |
| GET | `/api/auth/me` | current user |
| POST | `/api/scan` | multipart `image`, `lang`, optional `lat`/`lon` → full report |
| GET | `/api/scans` | your scan history |
| GET | `/api/scans/{id}` | one scan |
| POST | `/api/ask` | `{question, lang, scan_id?}` → advice |
| POST | `/api/transcribe` | multipart `audio`, `lang` → text |
| GET | `/api/health` | model + LLM status |

## Config (env vars)

`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `MODEL_PATH`, `CONF_THRESHOLD` (0.35), `IOU_THRESHOLD` (0.45), `CLASS_THRESHOLDS` (`{"rotten_banana": 0.85}`), `GROQ_API_KEY`, `LLM_MODEL`, `ASR_MODEL`, `DEFAULT_LAT`/`DEFAULT_LON` (Mingora, Swat), `DEMO_EMAIL`, `DEMO_PASSWORD`.

## Roadmap

- Peach, persimmon and pear classes from orchard photos collected in Swat
- Bruise / scab level grading, not just fresh vs rotten
- RAG over local storage and handling guides (ChromaDB + bge-m3)
- Self-hosted Qwen2.5-7B via Ollama, offline-first PWA
- Feedback loop: corrected labels → retraining tracked in MLflow
