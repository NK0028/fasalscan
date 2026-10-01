import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { t, RTL_LANGS as RTL, errorText, fruitName } from "../i18n.js";

const SUGGESTIONS = {
  en: ["Should I sell this today or wait?", "How do I store these to last longer?", "What can I do with the rotten ones?"],
  ur: ["کیا آج بیچ دوں یا انتظار کروں؟", "انہیں زیادہ دن کیسے رکھوں؟", "خراب پھلوں کا کیا کروں؟"],
  ps: ["نن یې وپلورم که انتظار وکړم؟", "دا څنګه ډېر وخت وساتم؟", "د خرابو مېوو سره څه وکړم؟"],
};

function pickMime() {
  if (typeof MediaRecorder === "undefined") return null;
  const options = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  return options.find((m) => MediaRecorder.isTypeSupported?.(m)) || "";
}

export default function Ask({ lang, lastScan: scanFromTab }) {
  const [latest, setLatest] = useState(null);
  const lastScan = scanFromTab || latest;
  // After a reload the Scan tab has nothing in memory, so use the newest saved scan.
  useEffect(() => {
    if (scanFromTab) return;
    api("/api/scans?limit=1").then((rows) => setLatest(rows?.[0] || null)).catch(() => {});
  }, [scanFromTab]);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const recRef = useRef(null);
  const chunksRef = useRef([]);
  const endRef = useRef(null);
  const canRecord = Boolean(navigator.mediaDevices?.getUserMedia) && pickMime() !== null;
  const rtl = RTL.has(lang);
  const s = t(lang);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  useEffect(() => () => recRef.current?.stream?.getTracks().forEach((t) => t.stop()), []);

  async function send(question) {
    const q = question.trim();
    if (!q || busy) return;
    setError("");
    setText("");
    setMessages((m) => [...m, { role: "user", text: q, lang }]);
    setBusy(true);
    try {
      const res = await api("/api/ask", {
        method: "POST",
        json: { question: q, lang, scan_id: lastScan?.id ?? null },
      });
      setMessages((m) => [...m, { role: "bot", text: res.answer, lang, ai: res.ai }]);
    } catch (err) {
      setError(errorText(lang, err));
    } finally {
      setBusy(false);
    }
  }

  async function startRecording() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = pickMime();
      const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunksRef.current = [];
      rec.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const type = rec.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        if (blob.size < 1000) {
          setError(s.errTooShort);
          return;
        }
        const ext = type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm";
        const form = new FormData();
        form.append("audio", blob, `speech.${ext}`);
        form.append("lang", lang);
        setBusy(true);
        try {
          const res = await api("/api/transcribe", { method: "POST", form });
          setBusy(false);
          await send(res.text);
        } catch (err) {
          setError(errorText(lang, err));
          setBusy(false);
        }
      };
      rec.start();
      recRef.current = rec;
      setRecording(true);
    } catch {
      setError(s.errMic);
    }
  }

  function stopRecording() {
    recRef.current?.state === "recording" && recRef.current.stop();
    setRecording(false);
  }

  return (
    <section className="ask">
      <p className={`muted ${rtl ? "rtl" : ""}`} dir={rtl ? "rtl" : "ltr"}>
        {lastScan
          ? s.askAbout(lastScan.total, fruitName(lang, lastScan.fruit, "fruitAttr"), lastScan.grade)
          : s.askNoScan}
      </p>

      <div className="chat" aria-live="polite">
        {messages.length === 0 && (
          <div className="suggestions">
            {(SUGGESTIONS[lang] || SUGGESTIONS.en).map((s) => (
              <button
                key={s}
                className={`chip ${rtl ? "rtl" : ""}`}
                dir={rtl ? "rtl" : "ltr"}
                onClick={() => send(s)}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => {
          const r = RTL.has(m.lang);
          return (
            <div key={i} className={`bubble ${m.role} ${r ? "rtl" : ""}`} dir={r ? "rtl" : "ltr"} lang={m.lang}>
              {m.text}
              {m.role === "bot" && m.ai === false && <span className="offline-note">{s.offline}</span>}
            </div>
          );
        })}
        {busy && <div className="bubble bot typing"><span /><span /><span /></div>}
        <div ref={endRef} />
      </div>

      {error && <p className="error">{error}</p>}

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          send(text);
        }}
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={s.askPlaceholder}
          dir={rtl ? "rtl" : "ltr"}
          className={rtl ? "rtl" : ""}
          disabled={busy || recording}
        />
        {canRecord && (
          <button
            type="button"
            className={`mic ${recording ? "on" : ""}`}
            onClick={recording ? stopRecording : startRecording}
            disabled={busy}
            aria-label={recording ? s.micStop : s.micStart}
          >
            {recording ? "■" : "🎤"}
          </button>
        )}
        <button className="btn primary" type="submit" disabled={busy || recording || !text.trim()}>
          {s.send}
        </button>
      </form>
    </section>
  );
}
