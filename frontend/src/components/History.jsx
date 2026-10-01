import { useEffect, useState } from "react";
import { api } from "../api.js";
import ResultCard from "./ResultCard.jsx";
import { t, RTL_LANGS, errorText, fruitName } from "../i18n.js";

function when(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function History({ lang }) {
  const s = t(lang);
  const rtl = RTL_LANGS.has(lang);
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api("/api/scans")
      .then(setItems)
      .catch((e) => setError(e));
  }, []);

  if (error) return <p className="error">{errorText(lang, error)}</p>;
  if (!items) return <p className={`muted center ${rtl ? "rtl" : ""}`}>{s.histLoading}</p>;
  if (!items.length) return <p className={`muted center ${rtl ? "rtl" : ""}`}>{s.histEmpty}</p>;

  return (
    <section className="history">
      {items.map((scan) => (
        <div key={scan.id} className="hist-item">
          <button className="hist-row" onClick={() => setOpen(open === scan.id ? null : scan.id)} aria-expanded={open === scan.id}>
            <span className={`mini-grade grade-${scan.grade}`}>{scan.grade}</span>
            <span className="hist-main">
              <strong>{scan.total} {fruitName(lang, scan.fruit)}</strong>
              <span className="muted" dir="ltr">{when(scan.created_at)}</span>
            </span>
            <span className="hist-side">
              <span>{s.damagedPct(scan.reject_pct)}</span>
              <span className="muted">{scan.total ? s.daysApprox(scan.days_left) : "–"}</span>
            </span>
          </button>
          {open === scan.id && <ResultCard scan={scan} compact />}
        </div>
      ))}
    </section>
  );
}
