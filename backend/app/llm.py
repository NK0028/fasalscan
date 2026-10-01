"""Plain-language summaries, Q&A and speech-to-text.

Uses open-weight models (Llama 3.3 / Whisper) through Groq's OpenAI-compatible API.
If no key is configured, or the call fails, everything falls back to templates
so the demo never breaks.
"""

import json
import logging
import re

import httpx

from .config import settings

log = logging.getLogger("fasalscan.llm")

LANG_NAMES = {"en": "English", "ur": "Urdu (Urdu script)", "ps": "Pashto (Pashto script)"}

ADVICE = {
    "en": {
        "hold": "The lot is in good shape. Keep it somewhere cool and shaded and you can wait for a better rate.",
        "sell_soon": "Quality is fine, but don't sit on it. Try to sell within the next few days.",
        "sell_now": "This won't last long. Sell today or tomorrow.",
        "sort_first": "Pick out the rotten pieces before you sell. Left in the crate, they spoil the rest.",
        "process": "Too much of this lot is damaged for the fresh market. Sort it and sell the rest for juice, pulp or drying.",
        "none": "I couldn't find any fruit in this photo. Try again closer to the crate, in daylight.",
    },
    "ur": {
        "hold": "مال اچھی حالت میں ہے۔ ٹھنڈی اور سایہ دار جگہ پر رکھیں تو بہتر ریٹ کا انتظار کیا جا سکتا ہے۔",
        "sell_soon": "معیار ٹھیک ہے، لیکن زیادہ دیر نہ رکھیں۔ اگلے چند دنوں میں بیچ دیں۔",
        "sell_now": "یہ مال زیادہ دن نہیں چلے گا۔ آج یا کل ہی بیچ دیں۔",
        "sort_first": "بیچنے سے پہلے خراب پھل الگ کر لیں، ورنہ باقی پھل بھی خراب ہو جائیں گے۔",
        "process": "اس مال کا بڑا حصہ خراب ہے۔ چھانٹی کر کے باقی جوس یا گودے کے لیے بیچ دیں۔",
        "none": "اس تصویر میں کوئی پھل نظر نہیں آیا۔ دن کی روشنی میں کریٹ کے قریب سے دوبارہ تصویر لیں۔",
    },
}

FRUIT_UR = {
    "apple": "سیب", "banana": "کیلا", "orange": "مالٹا", "peach": "آڑو", "mango": "آم",
    "pear": "ناشپاتی", "plum": "آلوچہ", "apricot": "خوبانی", "persimmon": "جاپانی پھل",
    "tomato": "ٹماٹر", "guava": "امرود", "pomegranate": "انار", "grape": "انگور",
}

HANDLING_NOTES = """Practical storage notes (use only if relevant):
- Apples last much longer in cold storage (0-4°C); at room temperature they soften within about 1-2 weeks.
- Apples and bananas give off ethylene; keep them away from other fruit to slow ripening.
- One rotten fruit spreads mould to its neighbours; sort crates before transport.
- Peaches, apricots and plums bruise easily: shallow crates, no stacking more than 2-3 layers.
- Avoid packing fruit wet; moisture speeds up rot.
- Shade the crates during transport; direct sun on a truck can add several degrees inside the crate.
- Damaged fruit can still be sold for juice, jam, pulp or drying instead of being thrown away."""


def _fmt_days(d: float) -> str:
    return str(int(d)) if float(d).is_integer() else str(d)


def template_summary(report: dict, weather: dict, lang: str) -> str:
    lang = "ur" if lang in ("ur", "ps") else "en"
    action = ADVICE[lang][report["action"]]
    if report["total"] == 0:
        return action
    days = _fmt_days(report["days_left"])
    temp = weather.get("outlook_c", weather["temp_c"])
    total, rotten = report["total"], report["rotten"]
    if lang == "ur":
        fruit = FRUIT_UR.get(report["fruit"], report["fruit"])
        damaged = "کوئی خراب نہیں" if rotten == 0 else f"{rotten} خراب ہیں ({report['reject_pct']}٪)"
        return (
            f"تصاویر میں {total} {fruit} ملے، {damaged}۔ گریڈ: {report['grade']}۔ "
            f"اگلے چند دنوں کے موسم (تقریباً {temp}°C) میں یہ اندازاً {days} دن ٹھیک رہیں گے۔ {action}"
        )
    noun = report["fruit"] if total == 1 else _plural(report["fruit"])
    if rotten == 0:
        damaged = "none of them damaged" if total > 1 else "no damage seen"
    elif rotten == total:
        damaged = "all of them damaged" if total > 1 else "and it is damaged"
    else:
        damaged = f"{rotten} of them damaged ({report['reject_pct']}%)"
    return (
        f"Found {total} {noun}, {damaged}. Grade {report['grade']} ({report['grade_label']}). "
        f"With the next few days around {temp}°C, expect roughly {days} days before quality drops. {action}"
    )


def _plural(word: str) -> str:
    if word.endswith(("ch", "sh", "o")) and word != "mango":
        return word + "es"
    return word + "s"


def _facts(report: dict, weather: dict) -> dict:
    return {
        "fruit": report["fruit"],
        "total_detected": report["total"],
        "fresh": report["fresh"],
        "rotten": report["rotten"],
        "reject_percent": report["reject_pct"],
        "grade": f"{report['grade']} ({report['grade_label']})",
        "estimated_days_before_quality_drops": report["days_left"],
        "estimate_range_days": report["days_range"],
        "recommended_action": report["action"],
        "breakdown": report["breakdown"],
        "temperature_now_c": weather["temp_c"],
        "avg_temperature_next_days_c": weather.get("outlook_c"),
        "humidity_percent": weather["humidity"],
    }


async def _chat(messages: list[dict], max_tokens: int = 350) -> str | None:
    if not settings.GROQ_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            r = await client.post(
                f"{settings.GROQ_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        log.warning("LLM call failed: %s", exc)
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    return text or None


def _system(lang: str) -> str:
    return (
        "You are FasalScan, a practical assistant for fruit growers and small traders in Pakistan. "
        f"Always reply in {LANG_NAMES.get(lang, 'English')}. Speak simply, like an experienced mandi "
        "trader would to a farmer. No markdown, no bullet lists, no headings. Never invent numbers: "
        "only use the facts you are given, and call shelf life an estimate.\n\n" + HANDLING_NOTES
    )


async def summarise(report: dict, weather: dict, lang: str) -> str:
    if report["total"] == 0:
        return template_summary(report, weather, lang)
    answer = await _chat([
        {"role": "system", "content": _system(lang)},
        {"role": "user", "content": (
            "Here is the result of scanning a crate photo:\n"
            f"{json.dumps(_facts(report, weather), ensure_ascii=False)}\n\n"
            "Write 3 to 4 short sentences: what the lot looks like, how long it will roughly hold up, "
            "and what to do next."
        )},
    ])
    return answer or template_summary(report, weather, lang)


async def ask(question: str, report: dict | None, weather: dict | None, lang: str) -> tuple[str, bool]:
    context = (
        f"Latest scan:\n{json.dumps(_facts(report, weather), ensure_ascii=False)}"
        if report and weather else "The user has not scanned anything yet."
    )
    answer = await _chat([
        {"role": "system", "content": _system(lang)},
        {"role": "user", "content": f"{context}\n\nQuestion: {question}\n\nAnswer in at most 5 sentences."},
    ], max_tokens=400)
    if answer:
        return answer, True
    if report and weather:
        return template_summary(report, weather, lang), False
    fallback = {
        "en": "The advisor is offline right now. Scan a crate first and I'll give you the grade and shelf-life estimate.",
        "ur": "مشیر ابھی دستیاب نہیں۔ پہلے کریٹ کی تصویر سکین کریں، میں گریڈ اور اندازاً دن بتا دوں گا۔",
    }
    return fallback["ur" if lang in ("ur", "ps") else "en"], False


async def transcribe(audio: bytes, filename: str, content_type: str, lang: str) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("Voice input needs GROQ_API_KEY on the server.")
    data = {"model": settings.ASR_MODEL, "response_format": "json", "temperature": "0"}
    if lang in ("ur", "ps", "en"):
        data["language"] = lang
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT + 10) as client:
        r = await client.post(
            f"{settings.GROQ_BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            data=data,
            files={"file": (filename, audio, content_type or "audio/webm")},
        )
        r.raise_for_status()
        return r.json().get("text", "").strip()
