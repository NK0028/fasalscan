"""YOLOv8 ONNX inference with plain NumPy + Pillow (no OpenCV, keeps the image small)."""

import ast
import logging
import re
from pathlib import Path

import numpy as np
from PIL import Image

from .config import settings

log = logging.getLogger("fasalscan.detector")

KNOWN_FRUITS = [
    "apple", "banana", "orange", "peach", "mango", "pear", "plum", "apricot",
    "persimmon", "tomato", "guava", "pomegranate", "grape", "strawberry", "lemon",
]
ROTTEN_WORDS = ("rotten", "rot", "spoiled", "stale", "bad", "defect")


def parse_label(raw: str) -> tuple[str, str]:
    """'rottenbanana' / 'Rotten_Banana' / 'fresh apples' -> ('rotten'|'fresh', fruit)."""
    name = re.sub(r"[^a-z]", "", raw.lower())
    state = "rotten" if any(w in name for w in ROTTEN_WORDS) else "fresh"
    fruit = next((f for f in KNOWN_FRUITS if f in name), None)
    if fruit is None:
        fruit = re.sub(r"^(fresh|rotten|rot|spoiled|stale|bad|defect)", "", name).rstrip("s") or "fruit"
    return state, fruit


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_thr: float) -> list[int]:
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1).clip(0) * (y2 - y1).clip(0)
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = (xx2 - xx1).clip(0) * (yy2 - yy1).clip(0)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        order = order[1:][iou <= iou_thr]
    return keep


def _merge(boxes: np.ndarray, scores: np.ndarray, iou_thr: float, ios_thr: float = 0.7) -> list[int]:
    """Class-agnostic NMS that also drops a box mostly contained in a stronger one
    (same fruit seen by the full pass and by a tile, or fresh/rotten double labels)."""
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = scores.argsort()[::-1]
    keep: list[int] = []
    for i in order:
        ok = True
        for j in keep:
            xx1, yy1 = max(boxes[i, 0], boxes[j, 0]), max(boxes[i, 1], boxes[j, 1])
            xx2, yy2 = min(boxes[i, 2], boxes[j, 2]), min(boxes[i, 3], boxes[j, 3])
            inter = max(0.0, xx2 - xx1) * max(0.0, yy2 - yy1)
            if inter / (areas[i] + areas[j] - inter + 1e-9) > iou_thr or inter / (min(areas[i], areas[j]) + 1e-9) > ios_thr:
                ok = False
                break
        if ok:
            keep.append(int(i))
    return keep


class Detector:
    def __init__(self, model_path: str):
        self.available = False
        self.names: dict[int, str] = {}
        self.input_size = 640
        self.normalized_boxes: bool | None = None  # detected on first inference
        path = Path(model_path)
        if not path.exists():
            log.warning("Model not found at %s, scanning disabled", path)
            return

        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
        inp = self.session.get_inputs()[0]
        self.input_name = inp.name
        h = inp.shape[2] if len(inp.shape) == 4 else None
        if isinstance(h, int) and h > 0:
            self.input_size = h

        meta = self.session.get_modelmeta().custom_metadata_map
        if "names" in meta:
            try:
                self.names = {int(k): str(v) for k, v in ast.literal_eval(meta["names"]).items()}
            except (ValueError, SyntaxError):
                log.warning("Could not parse class names from model metadata")
        if not self.names and settings.CLASS_NAMES:
            self.names = dict(enumerate(settings.CLASS_NAMES))

        self.available = True
        log.info("Loaded %s (input %d, classes %s)", path.name, self.input_size, self.names)

    def _letterbox(self, img: Image.Image) -> tuple[np.ndarray, float, int, int]:
        s = self.input_size
        w, h = img.size
        r = min(s / w, s / h)
        nw, nh = round(w * r), round(h * r)
        canvas = Image.new("RGB", (s, s), (114, 114, 114))
        px, py = (s - nw) // 2, (s - nh) // 2
        canvas.paste(img.resize((nw, nh), Image.BILINEAR), (px, py))
        arr = np.asarray(canvas, dtype=np.float32) / 255.0
        return arr.transpose(2, 0, 1)[None], r, px, py

    def _threshold_for(self, state: str, fruit: str) -> float:
        return settings.CLASS_THRESHOLDS.get(f"{state}_{fruit}", settings.CONF_THRESHOLD)

    def _infer(self, img: Image.Image) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """One forward pass. Returns (boxes_xyxy_px, conf, cls) in img coordinates."""
        w, h = img.size
        empty = (np.zeros((0, 4), np.float32), np.zeros(0, np.float32), np.zeros(0, int))
        tensor, r, px, py = self._letterbox(img)
        out = self.session.run(None, {self.input_name: tensor})[0]
        pred = np.squeeze(out, 0)
        if pred.shape[0] < pred.shape[1]:  # (4+nc, N) -> (N, 4+nc)
            pred = pred.T
        class_scores = pred[:, 4:]
        cls = class_scores.argmax(1)
        conf = class_scores.max(1)

        mask = conf >= min([settings.CONF_THRESHOLD, *settings.CLASS_THRESHOLDS.values()])
        if not mask.any():
            return empty
        pred, cls, conf = pred[mask], cls[mask], conf[mask]

        # Newer Ultralytics exports can emit boxes normalised to 0-1 instead of pixels.
        if self.normalized_boxes is None:
            self.normalized_boxes = bool(pred[:, :4].max() <= 2.0)
        if self.normalized_boxes:
            pred = pred.copy()
            pred[:, :4] *= self.input_size
        cx, cy, bw, bh = pred[:, 0], pred[:, 1], pred[:, 2], pred[:, 3]
        boxes = np.stack([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 1)
        boxes[:, [0, 2]] = ((boxes[:, [0, 2]] - px) / r).clip(0, w)
        boxes[:, [1, 3]] = ((boxes[:, [1, 3]] - py) / r).clip(0, h)

        keep = _nms(boxes + cls[:, None].astype(np.float32) * 1e5, conf, settings.IOU_THRESHOLD)
        keep = [
            i for i in keep
            if conf[i] >= self._threshold_for(*parse_label(self.names.get(int(cls[i]), "")))
            and boxes[i, 2] - boxes[i, 0] >= 2 and boxes[i, 3] - boxes[i, 1] >= 2
        ]
        if not keep:
            return empty
        k = np.array(keep)
        return boxes[k], conf[k], cls[k]

    def _tiles(self, w: int, h: int) -> list[tuple[int, int, int, int]]:
        """Overlapping tiles so small fruit in a crate photo get enough pixels."""
        if max(w, h) < 2 * self.input_size * 0.8:
            return []
        n_x = 3 if w >= 3 * self.input_size else 2
        n_y = 3 if h >= 3 * self.input_size else 2
        tw, th = int(w / n_x * 1.3), int(h / n_y * 1.3)
        xs = np.linspace(0, w - tw, n_x).astype(int)
        ys = np.linspace(0, h - th, n_y).astype(int)
        return [(x, y, x + tw, y + th) for y in ys for x in xs]

    def predict(self, img: Image.Image) -> list[dict]:
        if not self.available:
            raise RuntimeError("Model not loaded")
        w, h = img.size
        boxes, conf, cls = self._infer(img)
        all_b, all_c, all_k = [boxes], [conf], [cls]

        if settings.TILED_INFERENCE:
            for (x1, y1, x2, y2) in self._tiles(w, h):
                tb, tc, tk = self._infer(img.crop((x1, y1, x2, y2)))
                if not len(tb):
                    continue
                tw, th = x2 - x1, y2 - y1
                edge = 0.02 * max(tw, th)
                # drop boxes cut by an inner tile edge: they are partial fruit
                cut = (
                    ((tb[:, 0] < edge) & (x1 > 0)) | ((tb[:, 2] > tw - edge) & (x2 < w))
                    | ((tb[:, 1] < edge) & (y1 > 0)) | ((tb[:, 3] > th - edge) & (y2 < h))
                )
                tb, tc, tk = tb[~cut], tc[~cut], tk[~cut]
                if len(tb):
                    all_b.append(tb + np.array([x1, y1, x1, y1], np.float32))
                    all_c.append(tc)
                    all_k.append(tk)

        boxes, conf, cls = np.concatenate(all_b), np.concatenate(all_c), np.concatenate(all_k)
        if not len(boxes):
            return []
        keep = _merge(boxes, conf, settings.IOU_THRESHOLD)
        results = []
        for i in keep:
            raw = self.names.get(int(cls[i]), f"class_{int(cls[i])}")
            state, fruit = parse_label(raw)
            x1, y1, x2, y2 = boxes[i].tolist()
            results.append({
                "label": raw,
                "state": state,
                "fruit": fruit,
                "confidence": round(float(conf[i]), 3),
                "box": [round(x1 / w, 4), round(y1 / h, 4), round(x2 / w, 4), round(y2 / h, 4)],
            })
        results.sort(key=lambda d: d["confidence"], reverse=True)
        return results
