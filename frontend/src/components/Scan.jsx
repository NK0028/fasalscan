import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import ResultCard from "./ResultCard.jsx";
import { t } from "../i18n.js";

// Sample lots: drop these files into frontend/public/samples/. A lot whose cover
// (first file) is missing is hidden.
const SAMPLE_LOTS = [
  { label: "Apples", files: ["apple-1.jpg", "apple-2.jpg", "apple-3.jpg"] },
  { label: "Oranges", files: ["orange-1.jpg", "orange-2.jpg", "orange-3.jpg", "orange-4.jpg"] },
  { label: "Bananas", files: ["banana-1.jpg", "banana-2.jpg", "banana-3.jpg", "banana-4.jpg"] },
];

const MAX_SIDE = 1280;
const MAX_PHOTOS = 12;
const TIP = "Tip: pick 4-8 fruit at random from the crate and photograph each one close up. More photos, fairer grade.";

async function compress(file) {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.85));
    return blob ? new File([blob], "scan.jpg", { type: "image/jpeg" }) : file;
  } catch {
    return file; // old browsers: send as-is, server handles it
  }
}

function getPosition() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => resolve(null),
      { timeout: 6000, maximumAge: 600000 }
    );
  });
}

function previewsOf(scan) {
  if (!scan) return [];
  if (Array.isArray(scan.previews)) return scan.previews;
  return scan.preview ? [scan.preview] : []; // scans stored before multi-photo
}

function plural(n, word) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

export default function Scan({ lang, onScanned, lastScan, user }) {
  // Each photo: { url, file }. Photos restored from lastScan have file === null.
  const [photos, setPhotos] = useState(() => previewsOf(lastScan).map((url) => ({ url, file: null })));
  const [result, setResult] = useState(lastScan || null);
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [useLocation, setUseLocation] = useState(false);
  const [visibleLots, setVisibleLots] = useState(SAMPLE_LOTS);
  const cameraRef = useRef(null);
  const galleryRef = useRef(null);

  // Latest values for the unmount cleanup.
  const photosRef = useRef(photos);
  const lastScanRef = useRef(lastScan);
  photosRef.current = photos;
  lastScanRef.current = lastScan;

  // Revoke an object URL unless the parent's lastScan still shows it.
  function release(url) {
    if (url?.startsWith("blob:") && !previewsOf(lastScanRef.current).includes(url)) URL.revokeObjectURL(url);
  }

  useEffect(() => () => photosRef.current.forEach((p) => release(p.url)), []);

  const room = MAX_PHOTOS - photos.length;
  const locked = busy || adding || Boolean(result);

  async function addFiles(list) {
    const all = Array.from(list || []);
    if (!all.length) return;
    const images = all.filter((f) => f.type.startsWith("image/"));
    const free = MAX_PHOTOS - photosRef.current.length;
    const take = images.slice(0, Math.max(0, free));
    if (images.length < all.length) setError("Some files weren't images and were skipped.");
    else if (take.length < images.length) setError(`Up to ${MAX_PHOTOS} photos per scan, extra ones were skipped.`);
    else setError("");
    if (!take.length) return;

    setAdding(true);
    try {
      const made = [];
      for (const f of take) {
        const small = await compress(f);
        made.push({ file: small, url: URL.createObjectURL(small) });
      }
      setPhotos((prev) => [...prev, ...made].slice(0, MAX_PHOTOS));
    } finally {
      setAdding(false);
    }
  }

  function onInput(e) {
    addFiles(e.target.files);
    e.target.value = ""; // allow picking the same file again
  }

  function removePhoto(i) {
    const gone = photos[i];
    if (!gone) return;
    release(gone.url);
    setPhotos((prev) => prev.filter((p) => p !== gone));
  }

  async function pickLot(lot) {
    setAdding(true);
    setError("");
    try {
      const files = await Promise.all(
        lot.files.map(async (name) => {
          try {
            const res = await fetch(`/samples/${name}`);
            if (!res.ok) return null;
            const blob = await res.blob();
            return new File([blob], name, { type: blob.type || "image/jpeg" });
          } catch {
            return null;
          }
        })
      );
      const ok = files.filter(Boolean);
      if (!ok.length) throw new Error();
      photosRef.current.forEach((p) => release(p.url));
      photosRef.current = [];
      setPhotos([]);
      setResult(null);
      setAdding(false);
      await addFiles(ok);
    } catch {
      setError("Couldn't load that sample.");
    } finally {
      setAdding(false);
    }
  }

  async function analyse() {
    const files = photos.map((p) => p.file).filter(Boolean);
    if (!files.length) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      files.forEach((f, i) => form.append("images", f, `photo-${i + 1}.jpg`));
      form.append("lang", lang);
      if (useLocation) {
        const pos = await getPosition();
        if (pos) {
          form.append("lat", String(pos.lat));
          form.append("lon", String(pos.lon));
        }
      }
      const data = await api("/api/scan", { method: "POST", form, timeoutMs: 90000 + files.length * 15000 });
      const previews = photos.map((p) => p.url);
      // The previous lastScan's photos are no longer shown anywhere once replaced.
      const old = previewsOf(lastScanRef.current).filter((u) => !previews.includes(u));
      const withPreviews = { ...data, previews };
      setResult(withPreviews);
      onScanned(withPreviews);
      lastScanRef.current = withPreviews;
      old.forEach((u) => u.startsWith("blob:") && URL.revokeObjectURL(u));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    photos.forEach((p) => release(p.url));
    setPhotos([]);
    setResult(null);
    setError("");
  }

  const hasPhotos = photos.length > 0;

  return (
    <section className="scan">
      {!hasPhotos && !result && (
        <>
          <p className="hello">Salam, {user.name.split(" ")[0]}. Pick a few fruit from the crate and snap each one close up, in daylight.</p>
          <div className="dropzone">
            <span className="dz-icon" aria-hidden>📷</span>
            <span className="dz-title">Photograph your fruit</span>
            <span className="dz-sub">Apples, bananas and oranges in this version</span>
            <div className="dz-actions">
              <button className="btn primary" onClick={() => cameraRef.current?.click()} disabled={adding}>
                Take photo
              </button>
              <button className="btn ghost" onClick={() => galleryRef.current?.click()} disabled={adding}>
                Choose photos
              </button>
            </div>
          </div>
          <p className="tip">{TIP}</p>

          {visibleLots.length > 0 && (
            <div className="samples">
              <span className="muted">No fruit nearby? Try a sample lot:</span>
              <div className="sample-row">
                {visibleLots.map((lot) => (
                  <button key={lot.label} className="sample" onClick={() => pickLot(lot)} disabled={adding}>
                    <img
                      src={`/samples/${lot.files[0]}`}
                      alt={lot.label}
                      onError={() => setVisibleLots((v) => v.filter((x) => x.label !== lot.label))}
                    />
                    <span>{lot.label} · {lot.files.length} photos</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <input ref={cameraRef} type="file" accept="image/*" capture="environment" hidden onChange={onInput} />
      <input ref={galleryRef} type="file" accept="image/*" multiple hidden onChange={onInput} />

      {(hasPhotos || result) && (
        <>
          {!result && (
            <div className="photo-head">
              <span>{plural(photos.length, "photo")}</span>
              <span className="muted">max {MAX_PHOTOS}</span>
            </div>
          )}

          <div className="photo-area">
            <div className={`photo-grid ${result ? "done" : ""}`}>
              {photos.map((p, i) => {
                const dets = result ? (result.detections || []).filter((d) => (d.image ?? 0) === i) : [];
                return (
                  <figure key={p.url} className="photo-cell">
                    <div className={`preview ${result ? "" : "thumb"}`}>
                      <img src={p.url} alt={`Photo ${i + 1}`} />
                      {dets.map((d, j) => (
                        <div
                          key={j}
                          className={`box ${d.state} ${d.box[1] < 0.12 ? "label-in" : ""}`}
                          style={{
                            left: `${d.box[0] * 100}%`,
                            top: `${d.box[1] * 100}%`,
                            width: `${(d.box[2] - d.box[0]) * 100}%`,
                            height: `${(d.box[3] - d.box[1]) * 100}%`,
                          }}
                        >
                          <span>{d.state === "rotten" ? "rotten" : "fresh"} {Math.round(d.confidence * 100)}%</span>
                        </div>
                      ))}
                      {!result && (
                        <button
                          className="remove"
                          onClick={() => removePhoto(i)}
                          disabled={locked}
                          aria-label={`Remove photo ${i + 1}`}
                        >
                          ×
                        </button>
                      )}
                    </div>
                    {result && dets.length === 0 && <figcaption className="nothing">Nothing found</figcaption>}
                  </figure>
                );
              })}

              {!result && room > 0 && (
                <div className="add-tile">
                  <span className="add-plus" aria-hidden>+</span>
                  <button onClick={() => cameraRef.current?.click()} disabled={locked}>Take photo</button>
                  <button onClick={() => galleryRef.current?.click()} disabled={locked}>From gallery</button>
                </div>
              )}
            </div>
            {busy && (
              <div className="scanning">
                <span>Checking {plural(photos.length, "photo")}…</span>
              </div>
            )}
          </div>
        </>
      )}

      {hasPhotos && !result && (
        <div className="actions">
          <p className="tip">{TIP}</p>
          <label className="check">
            <input type="checkbox" checked={useLocation} onChange={(e) => setUseLocation(e.target.checked)} />
            Use my location for weather (default: Swat)
          </label>
          <div className="btn-row">
            <button className="btn ghost" onClick={reset} disabled={busy || adding}>Clear all</button>
            <button className="btn primary" onClick={analyse} disabled={busy || adding}>
              {busy ? "Scanning…" : adding ? "Adding…" : `Scan ${plural(photos.length, "photo")}`}
            </button>
          </div>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <ResultCard scan={result} />
          <button className="btn primary wide" onClick={reset}>{t(lang).scanAnother}</button>
        </>
      )}
    </section>
  );
}
