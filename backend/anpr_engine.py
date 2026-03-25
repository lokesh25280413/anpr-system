"""
License Plate Detection & OCR Pipeline
=======================================
Improvements over original:
- Multi-scale OCR with multiple preprocessing variants
- Plate text validation & cleaning (regex + length filter)
- Fuzzy deduplication (avoids near-duplicate plates like "AB1234" vs "AB1234.")
- Smart frame sampling based on motion detection
- Per-plate confidence scoring with best-result tracking
- Structured logging instead of raw print statements
- Graceful error handling throughout
- Clean separation of concerns
"""

import cv2
import os
import re
import logging
import easyocr
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import json

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("LPD")

# ─────────────────────────────────────────
# CONSTANTS / CONFIG
# ─────────────────────────────────────────
MODEL_PATH      = "license_plate_detector.pt"
YOLO_CONF       = 0.35       # detection confidence threshold
OCR_CONF        = 0.40       # OCR confidence threshold
FRAME_INTERVAL  = 0.5        # seconds between sampled frames
MIN_PLATE_CHARS = 4          # shortest acceptable plate text
MAX_PLATE_CHARS = 12         # longest acceptable plate text
FUZZY_SIM_THRESH= 0.85       # similarity to consider two plates duplicates
PLATE_REGEX     = re.compile(r'^[A-Z0-9]{4,12}$')   # tweak for your region

# ─────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────
@dataclass
class Detection:
    plate: str
    confidence: float
    frame_number: int
    timestamp: str
    image_path: str
    box: tuple         # (x1, y1, x2, y2)

@dataclass
class ProcessingStats:
    frames_processed: int = 0
    detections_attempted: int = 0
    plates_saved: int = 0
    duplicates_skipped: int = 0
    ocr_failures: int = 0

# ─────────────────────────────────────────
# MODEL LOADER
# ─────────────────────────────────────────
def load_models(model_path: str, use_gpu: bool = False):
    """Load YOLO and EasyOCR models with validation."""
    if not Path(model_path).exists():
        raise FileNotFoundError(f"YOLO model not found: {model_path}")

    log.info("Loading YOLO model...")
    yolo = YOLO(model_path)

    log.info(f"Loading EasyOCR (gpu={use_gpu})...")
    ocr = easyocr.Reader(['en'], gpu=use_gpu)

    return yolo, ocr

# ─────────────────────────────────────────
# PLATE TEXT VALIDATION
# ─────────────────────────────────────────
def clean_plate_text(raw: str) -> str:
    """Strip non-alphanumeric chars and uppercase."""
    return re.sub(r'[^A-Z0-9]', '', raw.upper())

def is_valid_plate(text: str) -> bool:
    """Return True if text looks like a real plate."""
    return bool(PLATE_REGEX.match(text))

def is_fuzzy_duplicate(plate: str, existing: set, threshold: float = FUZZY_SIM_THRESH) -> bool:
    """Return True if plate is too similar to an already-seen plate."""
    for seen in existing:
        ratio = SequenceMatcher(None, plate, seen).ratio()
        if ratio >= threshold:
            return True
    return False

# ─────────────────────────────────────────
# IMAGE PREPROCESSING VARIANTS
# ─────────────────────────────────────────
def preprocess_variants(img: np.ndarray) -> list:
    """
    Return multiple preprocessed versions of the plate image.
    EasyOCR will be run on each; best confidence wins.
    """
    variants = []

    # Upscale small plates — OCR accuracy degrades below ~100px wide
    h, w = img.shape[:2]
    if w < 200:
        scale = 200 / w
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. CLAHE (contrast-limited adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    variants.append(clahe_img)

    # 2. Bilateral filter + adaptive threshold
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 13, 3
    )
    variants.append(thresh)

    # 3. Otsu binarisation on CLAHE
    _, otsu = cv2.threshold(clahe_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(otsu)

    # 4. Sharpened grayscale
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)
    variants.append(sharp)

    # 5. Original colour (sometimes OCR does better in colour)
    variants.append(img)

    return variants

# ─────────────────────────────────────────
# OCR WITH BEST-OF-N STRATEGY
# ─────────────────────────────────────────
def best_ocr_result(reader: easyocr.Reader, img: np.ndarray) -> Optional[tuple]:
    """
    Run OCR on multiple preprocessed variants.
    Return (plate_text, confidence) for the highest-confidence valid result.
    """
    variants = preprocess_variants(img)
    best_text, best_conf = None, 0.0

    for variant in variants:
        try:
            results = reader.readtext(variant, detail=1, paragraph=False)
        except Exception as e:
            log.debug(f"OCR variant failed: {e}")
            continue

        for (_, text, conf) in results:
            plate = clean_plate_text(text)
            if conf > best_conf and is_valid_plate(plate):
                best_conf = conf
                best_text = plate

    if best_text and best_conf >= OCR_CONF:
        return best_text, best_conf
    return None

# ─────────────────────────────────────────
# SAVE RESULT
# ─────────────────────────────────────────
def save_detection(detection: Detection, save_folder: Path) -> None:
    """Persist the plate image and metadata."""
    stem = f"vehicle_{detection.plate}_{detection.frame_number}"
    img_path = save_folder / f"{stem}.jpg"
    meta_path = save_folder / f"{stem}.json"

    # Load saved image_path from detection (already saved during process)
    meta = asdict(detection)
    meta.pop("image_path")  # already on disk

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    log.info(f"✅  Saved  →  {detection.plate}  (conf={detection.confidence:.2f})")

# ─────────────────────────────────────────
# MOTION-BASED SMART SAMPLING
# ─────────────────────────────────────────
def has_significant_motion(prev: np.ndarray, curr: np.ndarray, threshold: float = 1.5) -> bool:
    """Return True if there is enough frame-to-frame change to warrant processing."""
    if prev is None:
        return True
    diff = cv2.absdiff(
        cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
    )
    return diff.mean() > threshold

# ─────────────────────────────────────────
# LOAD PREVIOUSLY SAVED PLATES
# ─────────────────────────────────────────
def load_existing_plates(save_folder: Path) -> set:
    plates = set()
    for meta_file in save_folder.glob("*.json"):
        try:
            with open(meta_file) as f:
                data = json.load(f)
                plates.add(data["plate"])
        except Exception:
            pass
    return plates

# ─────────────────────────────────────────
# MAIN PROCESSING PIPELINE
# ─────────────────────────────────────────
def process_video(
    video_path: str,
    model_path: str = MODEL_PATH,
    use_gpu: bool = False,
    results_dir: str = "results",
) -> list[Detection]:
    """
    Full pipeline: load video → detect plates → OCR → deduplicate → save.
    Returns list of Detection objects.
    """
    # ── Setup ──
    save_folder = Path(results_dir)
    save_folder.mkdir(parents=True, exist_ok=True)

    yolo, ocr_reader = load_models(model_path, use_gpu)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    sample_every = max(1, int(fps * FRAME_INTERVAL))

    detected_plates = load_existing_plates(save_folder)
    log.info(f"Loaded {len(detected_plates)} existing plate(s) from disk.")

    detections: list[Detection] = []
    stats = ProcessingStats()
    prev_frame = None
    frame_idx = 0

    log.info(f"🚀  Processing  →  {video_path}  @{fps:.1f}fps, sampling every {sample_every} frames")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # ── Interval sampling ──
        if frame_idx % sample_every != 0:
            continue

        # ── Motion gate ──
        if not has_significant_motion(prev_frame, frame):
            prev_frame = frame
            continue
        prev_frame = frame

        stats.frames_processed += 1

        # ── YOLO detection ──
        try:
            yolo_results = yolo(frame, conf=YOLO_CONF, verbose=False)
        except Exception as e:
            log.warning(f"YOLO failed on frame {frame_idx}: {e}")
            continue

        for r in yolo_results:
            if r.boxes is None:
                continue
            boxes = r.boxes.xyxy.cpu().numpy()
            log.debug(f"Frame {frame_idx}: {len(boxes)} box(es) found")

            for box in boxes:
                x1, y1, x2, y2 = map(int, box[:4])

                # Expand bounding box slightly to capture edges
                pad = 4
                x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                x2, y2 = min(frame.shape[1], x2 + pad), min(frame.shape[0], y2 + pad)

                plate_crop = frame[y1:y2, x1:x2]
                if plate_crop.size == 0:
                    continue

                stats.detections_attempted += 1

                # ── OCR ──
                ocr_result = best_ocr_result(ocr_reader, plate_crop)
                if ocr_result is None:
                    stats.ocr_failures += 1
                    log.debug(f"No valid OCR on frame {frame_idx}")
                    continue

                plate_text, plate_conf = ocr_result
                log.debug(f"OCR →  {plate_text}  ({plate_conf:.2f})")

                # ── Deduplication ──
                if is_fuzzy_duplicate(plate_text, detected_plates):
                    stats.duplicates_skipped += 1
                    log.debug(f"⚠️   Duplicate skipped: {plate_text}")
                    continue

                detected_plates.add(plate_text)
                stats.plates_saved += 1

                # ── Save image ──
                stem = f"vehicle_{plate_text}_{frame_idx}"
                img_path = save_folder / f"{stem}.jpg"
                cv2.imwrite(str(img_path), plate_crop)

                detection = Detection(
                    plate=plate_text,
                    confidence=round(plate_conf, 4),
                    frame_number=frame_idx,
                    timestamp=datetime.now().isoformat(),
                    image_path=str(img_path),
                    box=(x1, y1, x2, y2),
                )
                save_detection(detection, save_folder)
                detections.append(detection)

    cap.release()

    # ── Summary ──
    log.info("─" * 50)
    log.info(f"✅  Finished  →  {video_path}")
    log.info(f"   Frames processed  : {stats.frames_processed}")
    log.info(f"   Detections tried  : {stats.detections_attempted}")
    log.info(f"   Plates saved      : {stats.plates_saved}")
    log.info(f"   Duplicates skipped: {stats.duplicates_skipped}")
    log.info(f"   OCR failures      : {stats.ocr_failures}")
    log.info("─" * 50)

    return detections


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="License Plate Detector")
    parser.add_argument("video",           help="Path to input video file")
    parser.add_argument("--model",  default=MODEL_PATH,  help="YOLO model path")
    parser.add_argument("--gpu",    action="store_true",  help="Use GPU for OCR")
    parser.add_argument("--output", default="results",    help="Results folder")
    args = parser.parse_args()

    results = process_video(
        video_path=args.video,
        model_path=args.model,
        use_gpu=args.gpu,
        results_dir=args.output,
    )

    print(f"\n🏁  {len(results)} unique plate(s) detected.")
    for d in results:
        print(f"   {d.plate:12s}  conf={d.confidence:.2f}  frame={d.frame_number}")