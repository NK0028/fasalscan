const ACTION_LABEL = {
  hold: "Can hold for a better rate",
  sell_soon: "Sell within a few days",
  sell_now: "Sell today or tomorrow",
  sort_first: "Sort out rotten fruit first",
  process: "Send to processing",
  none: "No fruit detected",
};

const RTL = new Set(["ur", "ps"]);

function fmtDays(d) {
  return Number.isInteger(d) ? d : d.toFixed(1);
}

export default function ResultCard({ scan, compact = false }) {
  const rtl = RTL.has(scan.lang);
  const w = scan.weather;

  return (
    <article className={`result ${compact ? "compact" : ""}`}>
      <div className="result-top">
        <div className={`grade grade-${scan.grade}`}>
          <span className="grade-letter">{scan.grade}</span>
          <span className="grade-label">{scan.grade_label}</span>
        </div>
        <div className="stats">
          <div className="stat">
            <span className="stat-num">{scan.total}</span>
            <span className="stat-cap">
              {scan.fruit !== "unknown" ? `${scan.fruit}s found` : "found"}
              {scan.photos > 1 ? ` from ${scan.photos} photos` : ""}
            </span>
          </div>
          <div className="stat">
            <span className="stat-num bad">{scan.reject_pct}%</span>
            <span className="stat-cap">damaged</span>
          </div>
          <div className="stat">
            <span className="stat-num">{scan.total ? `~${fmtDays(scan.days_left)}` : "–"}</span>
            <span className="stat-cap">days left</span>
          </div>
        </div>
      </div>

      {scan.total > 0 && (
        <>
          <div className={`action-pill action-${scan.action}`}>{ACTION_LABEL[scan.action] || scan.action}</div>
          <div className="meter" aria-label={`${scan.fresh} fresh, ${scan.rotten} rotten`}>
            <div className="meter-fresh" style={{ flex: scan.fresh || 0.0001 }} />
            <div className="meter-rotten" style={{ flex: scan.rotten || 0.0001 }} />
          </div>
          <div className="meter-legend">
            <span><i className="dot fresh" /> {scan.fresh} fresh</span>
            <span><i className="dot rotten" /> {scan.rotten} rotten</span>
          </div>
        </>
      )}

      <p className={`summary ${rtl ? "rtl" : ""}`} dir={rtl ? "rtl" : "ltr"} lang={scan.lang}>
        {scan.summary}
      </p>

      {!compact && (
        <div className="details">
          {scan.breakdown?.length > 1 && (
            <div className="detail-row">
              <span>By fruit</span>
              <span>
                {scan.breakdown.map((b) => `${b.fruit}: ${b.fresh} fresh / ${b.rotten} rotten`).join(" · ")}
              </span>
            </div>
          )}
          {scan.total > 0 && (
            <div className="detail-row">
              <span>Shelf-life range</span>
              <span>{scan.days_range[0]}–{scan.days_range[1]} days (estimate)</span>
            </div>
          )}
          {w && (
            <div className="detail-row">
              <span>Weather used</span>
              <span>
                {w.temp_c}°C now · {w.outlook_c}°C avg next days · {w.humidity}% humidity
                {w.source === "default" ? " (default, live weather unavailable)" : ""}
              </span>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
