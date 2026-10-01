import { t, RTL_LANGS } from "../i18n.js";

function fmt(d) {
  const n = Number(d);
  return Number.isInteger(n) ? n : n.toFixed(1);
}

export default function ResultCard({ scan, compact = false }) {
  const s = t(scan.lang);
  const rtl = RTL_LANGS.has(scan.lang);
  const w = scan.weather;
  const textDir = rtl ? "rtl" : "ltr";

  return (
    <article className={`result ${compact ? "compact" : ""}`}>
      <div className="result-top">
        <div className={`grade grade-${scan.grade}`}>
          <span className="grade-letter">{scan.grade}</span>
          <span className="grade-label" dir={textDir}>{s.grade[scan.grade] || scan.grade_label}</span>
        </div>
        <div className="stats">
          <div className="stat">
            <span className="stat-num" dir="ltr">{scan.total}</span>
            <span className="stat-cap" dir={textDir}>{s.samples(scan.total, scan.photos || 1)}</span>
          </div>
          <div className="stat">
            <span className="stat-num bad" dir="ltr">{fmt(scan.reject_pct)}%</span>
            <span className="stat-cap" dir={textDir}>{s.damaged}</span>
          </div>
          <div className="stat">
            <span className="stat-num" dir="ltr">{scan.total ? `~${fmt(scan.days_left)}` : "–"}</span>
            <span className="stat-cap" dir={textDir}>{s.daysLeft}</span>
          </div>
        </div>
      </div>

      {scan.total > 0 && (
        <>
          <div className={`action-pill action-${scan.action}`} dir={textDir}>{s.action[scan.action] || scan.action}</div>
          <div className="meter" aria-label={`${scan.fresh} ${s.fresh}, ${scan.rotten} ${s.rotten}`}>
            <div className="meter-fresh" style={{ flex: scan.fresh || 0.0001 }} />
            <div className="meter-rotten" style={{ flex: scan.rotten || 0.0001 }} />
          </div>
          <div className="meter-legend" dir={textDir}>
            <span><i className="dot fresh" /> {scan.fresh} {s.fresh}</span>
            <span><i className="dot rotten" /> {scan.rotten} {s.rotten}</span>
          </div>
        </>
      )}

      <p className={`summary ${rtl ? "rtl" : ""}`} dir={textDir} lang={scan.lang}>
        {scan.summary}
      </p>

      {!compact && (
        <div className="details" dir={textDir}>
          {scan.breakdown?.length > 1 && (
            <div className="detail-row">
              <span>{s.byFruit}</span>
              <span>
                {scan.breakdown.map((b) => `${b.fruit}: ${b.fresh} ${s.fresh} / ${b.rotten} ${s.rotten}`).join(" · ")}
              </span>
            </div>
          )}
          {scan.total > 0 && (
            <div className="detail-row">
              <span>{s.shelfRange}</span>
              <span>{fmt(scan.days_range[0])}–{fmt(scan.days_range[1])} {s.days}</span>
            </div>
          )}
          {w && (
            <div className="detail-row">
              <span>{s.weather}</span>
              <span>{w.source === "seasonal" || w.source === "default" ? s.weatherSeasonal(w) : s.weatherLive(w)}</span>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
