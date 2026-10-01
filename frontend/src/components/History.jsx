import { useEffect, useState } from "react";
import { api } from "../api.js";
import ResultCard from "./ResultCard.jsx";

function when(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function History() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api("/api/scans")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!items) return <p className="muted center">Loading your scans…</p>;
  if (!items.length) return <p className="muted center">No scans yet. Your scanned crates will show up here.</p>;

  return (
    <section className="history">
      {items.map((s) => (
        <div key={s.id} className="hist-item">
          <button className="hist-row" onClick={() => setOpen(open === s.id ? null : s.id)} aria-expanded={open === s.id}>
            <span className={`mini-grade grade-${s.grade}`}>{s.grade}</span>
            <span className="hist-main">
              <strong>{s.total} {s.fruit !== "unknown" ? `${s.fruit}s` : "items"}</strong>
              <span className="muted">{when(s.created_at)}</span>
            </span>
            <span className="hist-side">
              <span>{s.reject_pct}% damaged</span>
              <span className="muted">{s.total ? `~${s.days_left} days` : "–"}</span>
            </span>
          </button>
          {open === s.id && <ResultCard scan={s} compact />}
        </div>
      ))}
    </section>
  );
}
