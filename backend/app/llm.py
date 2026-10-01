"""Plain-language summaries, Q&A and speech-to-text.

Uses open-weight models (Llama 3.3 / GPT-OSS / Whisper) through Groq's OpenAI-compatible API.
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

ADVICE["ps"] = {
    "hold": "مال په ښه حالت کې دی. په سړه او سیوري ځای کې یې وساتئ، د ښه نرخ انتظار کولی شئ.",
    "sell_soon": "کیفیت یې ښه دی، خو ډېر یې مه ساتئ. په راتلونکو څو ورځو کې یې وپلورئ.",
    "sell_now": "دا مال ډېر نه پاتې کېږي. نن یا سبا یې وپلورئ.",
    "sort_first": "د پلورلو نه مخکې خرابې مېوې جلا کړئ، که نه نورې به هم خرابې شي.",
    "process": "د دې مال ډېره برخه خرابه ده. جلا یې کړئ او پاتې د جوس یا ګودې لپاره وپلورئ.",
    "none": "په دې انځور کې هېڅ مېوه ونه موندل شوه. د ورځې په رڼا کې له نږدې بیا انځور واخلئ.",
}

# Urdu fruit names (singular, plural) and Pashto names.
FRUIT_UR = {
    "apple": ("سیب", "سیب"), "banana": ("کیلا", "کیلے"), "orange": ("مالٹا", "مالٹے"),
    "peach": ("آڑو", "آڑو"), "mango": ("آم", "آم"), "pear": ("ناشپاتی", "ناشپاتیاں"),
    "plum": ("آلوچہ", "آلوچے"), "apricot": ("خوبانی", "خوبانیاں"), "tomato": ("ٹماٹر", "ٹماٹر"),
    "guava": ("امرود", "امرود"), "pomegranate": ("انار", "انار"), "grape": ("انگور", "انگور"),
}
FRUIT_PS = {
    "apple": "مڼو", "banana": "کېلو", "orange": "مالټو", "peach": "شفتالو", "mango": "آم",
    "pear": "ناک", "plum": "آلوچې", "apricot": "زردآلو", "tomato": "رومیان", "grape": "انګور",
    "pomegranate": "انار", "guava": "امرود",
}

HANDLING_NOTES = """Practical storage notes (use only if relevant):
- Apples last much longer in cold storage (0-4°C); at room temperature they soften within about 1-2 weeks.
- Apples and bananas give off ethylene; keep them away from other fruit to slow ripening.
- One rotten fruit spreads mould to its neighbours; sort crates before transport.
- Peaches, apricots and plums bruise easily: shallow crates, no stacking more than 2-3 layers.
- Avoid packing fruit wet; moisture speeds up rot.
- Shade the crates during transport; direct sun on a truck can add several degrees inside the crate.
- Damaged fruit can still be sold for juice, jam, pulp or drying instead of being thrown away."""


def _num(x: float) -> str:
    """22.0 -> 22, 25.5 -> 25.5 (reads naturally inside a sentence)."""
    x = round(float(x), 1)
    return str(int(x)) if x.is_integer() else str(x)


def template_summary(report: dict, weather: dict, lang: str) -> str:
    lang = lang if lang in ADVICE else "en"
    action = ADVICE[lang][report["action"]]
    if report["total"] == 0:
        return action
    days = _num(report["days_left"])
    temp = _num(round(weather.get("outlook_c", weather["temp_c"])))
    pct = _num(report["reject_pct"])
    total, rotten = report["total"], report["rotten"]
    fruit_key = report["fruit"]

    if lang == "ur":
        sing, plur = FRUIT_UR.get(fruit_key, (fruit_key, fruit_key))
        damaged = (
            "کوئی بھی خراب نہیں" if rotten == 0
            else ("سب خراب ہیں" if rotten == total else f"{rotten} خراب {'ہے' if rotten == 1 else 'ہیں'} ({pct}٪)")
        )
        return (
            f"{plur if total > 1 else sing} کے {total} نمونے جانچے گئے، {damaged}۔ گریڈ: {report['grade']}۔ "
            f"اگلے چند دنوں کا اوسط درجہ حرارت تقریباً {temp}°C ہے، اس میں یہ اندازاً {days} دن ٹھیک رہیں گے۔ {action}"
        )
    if lang == "ps":
        fruit = FRUIT_PS.get(fruit_key, fruit_key)
        damaged = (
            "هېڅ یو خراب نه دی" if rotten == 0
            else ("ټول خراب دي" if rotten == total else f"{rotten} یې خراب {'دی' if rotten == 1 else 'دي'} ({pct}٪)")
        )
        return (
            f"د {fruit} {total} نمونې وکتل شوې، {damaged}. درجه: {report['grade']}. "
            f"د راتلونکو ورځو منځنۍ تودوخه شاوخوا {temp}°C ده، په دې کې به دا اټکلاً {days} ورځې سم پاتې شي. {action}"
        )

    noun = fruit_key if total == 1 else _plural(fruit_key)
    if rotten == 0:
        damaged = "none of them damaged" if total > 1 else "no damage seen"
    elif rotten == total:
        damaged = "all of them damaged" if total > 1 else "and it is damaged"
    else:
        damaged = f"{rotten} of them damaged ({pct}%)"
    return (
        f"Checked {total} {noun}, {damaged}. Grade {report['grade']} ({report['grade_label']}). "
        f"With the next few days averaging about {temp}°C, expect roughly {days} days before quality drops. {action}"
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


# Preferred order. The first one this API key can actually use is picked at runtime.
_PREFERRED_MODELS = [
    "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3-32b",
    "llama-3.1-8b-instant", "openai/gpt-oss-20b",
]
_last_error: dict = {"llm": None}
_available: dict = {"models": None}


async def _models(client: httpx.AsyncClient) -> list[str]:
    """Models this key can use, in our preferred order (cached after the first call)."""
    if _available["models"] is None:
        try:
            r = await client.get(
                f"{settings.GROQ_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            )
            r.raise_for_status()
            ids = {m["id"] for m in r.json().get("data", [])}
            wanted = [settings.LLM_MODEL] + [m for m in _PREFERRED_MODELS if m != settings.LLM_MODEL]
            chosen = [m for m in wanted if m in ids]
            # anything else that looks like a chat model, as a last resort
            chosen += sorted(m for m in ids if m not in chosen and not any(
                x in m for x in ("whisper", "guard", "orpheus", "tts", "safeguard")))
            _available["models"] = chosen
            log.info("LLM models usable with this key: %s", chosen[:6])
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("Could not list models: %s", exc)
            return [settings.LLM_MODEL] + [m for m in _PREFERRED_MODELS if m != settings.LLM_MODEL]
    return _available["models"]


def _payload(model: str, messages: list[dict], max_tokens: int) -> dict:
    body = {"model": model, "messages": messages, "temperature": 0.4}
    if "gpt-oss" in model:
        # reasoning models spend tokens thinking before they answer
        body.update({"reasoning_effort": "low", "include_reasoning": False, "max_completion_tokens": max_tokens + 1024})
    elif "qwen3" in model:
        body.update({"reasoning_effort": "none", "max_completion_tokens": max_tokens + 256})
    else:
        body["max_tokens"] = max_tokens
    return body


async def _chat(messages: list[dict], max_tokens: int = 350) -> str | None:
    if not settings.GROQ_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
        for model in (await _models(client))[:5]:
            try:
                r = await client.post(
                    f"{settings.GROQ_BASE_URL}/chat/completions",
                    headers=headers,
                    json=_payload(model, messages, max_tokens),
                )
            except httpx.HTTPError as exc:
                _last_error["llm"] = f"{type(exc).__name__}: {exc}"
                log.warning("LLM request failed (%s): %s", model, exc)
                return None
            if r.status_code == 429:
                _last_error["llm"] = f"{model}: rate limited"
                continue
            if r.status_code != 200:
                _last_error["llm"] = f"{model}: {r.status_code} {r.text[:200]}"
                log.warning("LLM call failed (%s): %s %s", model, r.status_code, r.text[:300])
                continue
            try:
                text = r.json()["choices"][0]["message"].get("content") or ""
            except (KeyError, IndexError, ValueError) as exc:
                _last_error["llm"] = f"{model}: bad response {exc}"
                continue
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
            if not text:
                _last_error["llm"] = f"{model}: empty answer"
                continue
            if model != settings.LLM_MODEL:
                log.info("Using LLM model %s", model)
                settings.LLM_MODEL = model  # stick with the one that works
            _last_error["llm"] = None
            return text
    return None


async def llm_status() -> dict:
    if not settings.GROQ_API_KEY:
        return {"configured": False}
    reply = await _chat([{"role": "user", "content": "Reply with the single word: ok"}], max_tokens=20)
    return {"configured": True, "ok": bool(reply), "model": settings.LLM_MODEL,
            "usable_models": (_available["models"] or [])[:6], "error": _last_error["llm"]}


GLOSSARY = {
    "ur": "Use everyday Urdu, not English loanwords when an Urdu word exists: apple سیب, banana کیلا/کیلے, "
          "orange مالٹا/مالٹے, pulp گودا, crate کریٹ, ventilated crate ہوادار کریٹ, cold storage کولڈ اسٹوریج, rotten خراب.",
    "ps": "Use everyday Pashto as spoken in Swat, not Urdu or English words when a Pashto word exists: apple مڼه/مڼې, "
          "banana کېله/کېلې, orange مالټه/مالټې, humidity لندبل, temperature تودوخه, crate کریټ, "
          "ventilated crate هوادار کریټ, rotten خراب. Watch gender agreement (اوسنۍ تودوخه).",
    "en": "",
}


def _system(lang: str) -> str:
    return (
        "You are FasalScan, a practical assistant for fruit growers and small traders in Swat, Pakistan. "
        f"Always reply in {LANG_NAMES.get(lang, 'English')}. Speak simply, like an experienced mandi trader "
        "talking to a farmer. No markdown, no lists, no headings. Write numbers with Western digits (0-9).\n"
        "Rules: never invent numbers, only use the facts given. The counts are SAMPLES the farmer photographed "
        "from a crate, not the whole crate, so say 'of the samples checked', never 'the crate has N fruit'. "
        "Shelf life is an estimate. When a recommended action is given, give exactly that one action and do not "
        "contradict it. Fruit always needs ventilated crates, never sealed or airtight boxes.\n"
        + GLOSSARY.get(lang, "") + "\n\n" + HANDLING_NOTES
    )


async def summarise(report: dict, weather: dict, lang: str) -> str:
    if report["total"] == 0:
        return template_summary(report, weather, lang)
    answer = await _chat([
        {"role": "system", "content": _system(lang)},
        {"role": "user", "content": (
            "Here is the result of scanning a crate photo:\n"
            f"{json.dumps(_facts(report, weather), ensure_ascii=False)}\n\n"
            "Write 3 short sentences: what the samples show, roughly how long the lot will hold up, "
            "and the one recommended action."
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
        lead = {
            "en": "The AI advisor is busy right now, so here is what your latest scan shows: ",
            "ur": "اے آئی مشیر ابھی مصروف ہے، آپ کے آخری سکین کا خلاصہ یہ ہے: ",
            "ps": "د AI مشاور اوس بوخت دی، ستاسو د وروستي سکین لنډیز دا دی: ",
        }.get(lang, "")
        return lead + template_summary(report, weather, lang), False
    fallback = {
        "en": "The advisor is offline right now. Scan a crate first and I'll give you the grade and shelf-life estimate.",
        "ur": "مشیر ابھی دستیاب نہیں۔ پہلے کریٹ کی تصویر سکین کریں، میں گریڈ اور اندازاً دن بتا دوں گا۔",
        "ps": "مشاور اوس شتون نه لري. لومړی د کریټ انځور سکین کړئ، زه به درجه او اټکلي ورځې درته ووایم.",
    }
    return fallback.get(lang, fallback["en"]), False


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
