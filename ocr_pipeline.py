#!/usr/bin/env python3
"""
Screenshot OCR Pipeline
=======================
Scans images in D:\\DataVault\\Screenshots, performs OCR via Tesseract,
extracts file paths / project structures, and writes structured outputs
to D:\\DataVault\\OCR_Output and D:\\DataVault\\Logs.

Usage:
    python ocr_pipeline.py [--screenshots DIR] [--output DIR] [--logs DIR]
"""

import os
import sys
import re
import csv
import json
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DEFAULT_SCREENSHOTS = Path(r"D:\DataVault\Screenshots")
DEFAULT_OCR_OUTPUT  = Path(r"D:\DataVault\OCR_Output")
DEFAULT_LOGS        = Path(r"D:\DataVault\Logs")

SUPPORTED_EXTS      = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
PROGRESS_INTERVAL   = 100   # log a status line every N files

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────
def setup_logging(logs_dir: Path) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"ocr_run_{stamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("ocr_pipeline")


# ──────────────────────────────────────────────────────────────────────────────
# TESSERACT SETUP
# ──────────────────────────────────────────────────────────────────────────────
def configure_tesseract(logger: logging.Logger) -> bool:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
        return True
    except Exception as e:
        logger.error(f"Tesseract not available at {TESSERACT_CMD}: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# IMAGE PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────
def preprocess(path: Path):
    """
    Return a PIL Image optimised for Tesseract.
    Converts to greyscale and applies Otsu thresholding when possible.
    Falls back to plain Pillow open if OpenCV fails.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image

        img = cv2.imread(str(path))
        if img is None:
            raise ValueError("cv2 returned None")

        # Upscale small images – Tesseract works best at ~300 DPI / 12px per char min
        h, w = img.shape[:2]
        if max(h, w) < 800:
            img = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

        gray      = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised  = cv2.fastNlMeansDenoising(gray, h=10)
        _, thresh = cv2.threshold(denoised, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)

    except Exception:
        from PIL import Image
        return Image.open(path).convert("RGB")


# ──────────────────────────────────────────────────────────────────────────────
# OCR
# ──────────────────────────────────────────────────────────────────────────────
#  PSM 6  = assume a single uniform block of text (best for screenshots)
#  OEM 3  = default engine (LSTM + legacy)
TESS_CONFIG = "--psm 6 --oem 3"


def ocr_image(path: Path) -> str:
    import pytesseract
    img  = preprocess(path)
    text = pytesseract.image_to_string(img, config=TESS_CONFIG)
    return text


# ──────────────────────────────────────────────────────────────────────────────
# REGEX PATTERNS
# ──────────────────────────────────────────────────────────────────────────────
# Each entry: (label, compiled_pattern)
PATTERNS = [
    (
        "windows_path",
        re.compile(
            r"""[A-Za-z]:[\\\/](?:[^\s\'"<>|*?\r\n\\\/]{1,120}[\\\/]){0,10}[^\s\'"<>|*?\r\n]{0,120}""",
            re.VERBOSE,
        ),
    ),
    (
        "unc_path",
        re.compile(r"""\\\\[\w.\-]+\\[\w.\-][^\s\'"<>|*?\r\n]*"""),
    ),
    (
        "project_indicator",
        re.compile(
            r"""\b(?:package\.json|requirements(?:[-_][\w.]+)?\.txt|Cargo\.toml|go\.mod|"""
            r"""pom\.xml|build\.gradle(?:\.kts)?|CMakeLists\.txt|Makefile|"""
            r"""\.gitignore|setup\.py|pyproject\.toml|composer\.json|Gemfile|"""
            r"""\.csproj|\.sln|angular\.json|tsconfig(?:[\w.]*)?\.json|"""
            r"""Dockerfile(?:[\w.]*)?|docker-compose(?:[\w.]*)?\.ya?ml)\b""",
            re.IGNORECASE,
        ),
    ),
    (
        "filename_with_ext",
        re.compile(
            r"""(?<!\w)[\w\-. ]{1,80}\.(?:py|js|ts|jsx|tsx|json|env|csproj|sln|"""
            r"""toml|yaml|yml|md|txt|csv|sql|sh|bat|ps1|rs|go|java|cs|cpp|c|h|"""
            r"""rb|php|vue|svelte|html|css|scss|less|xml|gradle|cmake|lock|log)(?!\w)""",
            re.IGNORECASE,
        ),
    ),
    (
        "terminal_command",
        re.compile(
            r"""(?m)^[ \t]*(?:\$|>|PS\s+[A-Za-z]:\\|[A-Za-z]:\\[^\n]*?>|npm |pip |"""
            r"""python |node |git |cd |mkdir |ls |dir |cat |echo |cargo |go |"""
            r"""dotnet |docker )[^\n]{3,120}""",
        ),
    ),
    (
        "url",
        re.compile(r"""https?://[^\s\'"<>\[\](){}\r\n]{5,200}"""),
    ),
    (
        "common_dir_fragment",
        re.compile(
            r"""(?:Users|AppData|Desktop|Documents|Projects|GitHub|repos?|src|source|"""
            r"""workspace(?:s)?|dev|code|work|sites|www|home|projects?)[\\\/][\w\-. ]{1,80}""",
            re.IGNORECASE,
        ),
    ),
]


def extract_matches(text: str, image_name: str) -> list[dict]:
    rows = []
    for label, pattern in PATTERNS:
        for m in pattern.finditer(text):
            value = m.group(0).strip().rstrip("\\/ ,;.")
            if len(value) < 3:
                continue

            start   = max(0, m.start() - 40)
            end     = min(len(text), m.end() + 40)
            snippet = text[start:end].replace("\n", " ").replace("\r", "").strip()

            # Derive filename when we have a path
            filename = ""
            if label in ("windows_path", "unc_path"):
                try:
                    filename = Path(value.replace("/", "\\")).name
                except Exception:
                    pass
            elif label == "filename_with_ext":
                filename = value.strip()

            rows.append(
                {
                    "ImageName":      image_name,
                    "PatternType":    label,
                    "DetectedPath":   value,
                    "FileName":       filename,
                    "ContextSnippet": snippet[:150],
                }
            )
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT CANDIDATE INFERENCE
# ──────────────────────────────────────────────────────────────────────────────
def infer_project_candidates(all_paths: list[str]) -> list[str]:
    """
    Score directory segments that look like project roots.
    Heuristics:
      - src / app / lib / backend / frontend / api inside a known path → +3
      - A path segment that matches a typical project name pattern at depth 3-5 → +1 per hit
    Returns a sorted "NNNx  path" list (top 60).
    """
    score: Counter = Counter()

    for raw in all_paths:
        norm  = raw.replace("/", "\\").rstrip("\\")
        parts = norm.split("\\")

        for i, part in enumerate(parts):
            # Structural markers that indicate one level above is the root
            if re.match(
                r"^(?:src|source|app|lib|backend|frontend|api|server|client|"
                r"web|mobile|core|common|shared|pkg|packages|modules)$",
                part,
                re.IGNORECASE,
            ):
                root = "\\".join(parts[:i])
                if root:
                    score[root] += 3

            # Depth 2-5 after a drive letter looks like a project root
            if (
                parts
                and re.match(r"^[A-Za-z]:$", parts[0])
                and 2 <= i <= 5
            ):
                score["\\".join(parts[: i + 1])] += 1

    return [f"{cnt:5d}x  {path}" for path, cnt in score.most_common(60)]


# ──────────────────────────────────────────────────────────────────────────────
# DEDUPLICATION PROGRESS TRACKING
# ──────────────────────────────────────────────────────────────────────────────
HASH_FILE = "processed_hashes.json"


def load_seen_hashes(logs_dir: Path) -> set:
    p = logs_dir / HASH_FILE
    if p.exists():
        try:
            return set(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def save_seen_hashes(logs_dir: Path, hashes: set) -> None:
    (logs_dir / HASH_FILE).write_text(
        json.dumps(sorted(hashes), indent=2), encoding="utf-8"
    )


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# OUTPUT COLLISION GUARD
# ──────────────────────────────────────────────────────────────────────────────
def unique_output_path(base: Path) -> Path:
    """Return base, or base_1, base_2 … if the file already exists."""
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    i = 1
    while True:
        candidate = base.parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Screenshot OCR Pipeline")
    p.add_argument("--screenshots", type=Path, default=DEFAULT_SCREENSHOTS)
    p.add_argument("--output",      type=Path, default=DEFAULT_OCR_OUTPUT)
    p.add_argument("--logs",        type=Path, default=DEFAULT_LOGS)
    p.add_argument(
        "--force",
        action="store_true",
        help="Reprocess images even if already in the hash cache",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    screenshots_dir: Path = args.screenshots
    ocr_output_dir:  Path = args.output
    logs_dir:        Path = args.logs

    logger = setup_logging(logs_dir)
    logger.info("=" * 60)
    logger.info("Screenshot OCR Pipeline — starting")
    logger.info(f"  Screenshots : {screenshots_dir}")
    logger.info(f"  OCR output  : {ocr_output_dir}")
    logger.info(f"  Logs        : {logs_dir}")
    logger.info("=" * 60)

    # ── Validate directories ──────────────────────────────────────────────────
    ocr_output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not screenshots_dir.exists():
        logger.error(f"Screenshots directory not found: {screenshots_dir}")
        logger.error("Create the folder or pass --screenshots <path>")
        sys.exit(1)

    # ── OCR engine check ─────────────────────────────────────────────────────
    if not configure_tesseract(logger):
        logger.error(
            "Tesseract not functional. Install from "
            "https://github.com/UB-Mannheim/tesseract/wiki "
            "or run: winget install UB-Mannheim.TesseractOCR"
        )
        sys.exit(1)

    # ── Collect images ────────────────────────────────────────────────────────
    logger.info(f"Scanning {screenshots_dir} …")
    all_images = sorted(
        p for p in screenshots_dir.rglob("*")
        if p.suffix.lower() in SUPPORTED_EXTS and p.is_file()
    )
    logger.info(f"Found {len(all_images):,} image(s)")

    # ── Load previously processed hashes ─────────────────────────────────────
    seen_hashes: set = set() if args.force else load_seen_hashes(logs_dir)
    logger.info(f"Cached hashes (already processed): {len(seen_hashes):,}")

    # ── Open / create CSV ─────────────────────────────────────────────────────
    csv_path          = logs_dir / "extracted_paths.csv"
    csv_is_new        = not csv_path.exists()
    csv_fh            = open(csv_path, "a", newline="", encoding="utf-8")
    CSV_FIELDS        = ["ImageName", "PatternType", "DetectedPath", "FileName", "ContextSnippet"]
    writer            = csv.DictWriter(csv_fh, fieldnames=CSV_FIELDS)
    if csv_is_new:
        writer.writeheader()

    # ── Processing loop ───────────────────────────────────────────────────────
    n_processed  = 0
    n_skipped    = 0
    n_failed     = 0
    all_win_paths: list[str] = []

    for img_path in all_images:
        try:
            img_hash = file_md5(img_path)
        except Exception as e:
            logger.warning(f"Cannot hash {img_path.name}: {e}")
            n_failed += 1
            continue

        if img_hash in seen_hashes:
            n_skipped += 1
            continue

        try:
            text = ocr_image(img_path)
        except Exception as e:
            logger.warning(f"OCR failed for {img_path.name}: {e}")
            n_failed += 1
            seen_hashes.add(img_hash)  # Don't retry broken images
            continue

        # ── Save raw .txt ─────────────────────────────────────────────────────
        out_txt = unique_output_path(ocr_output_dir / (img_path.stem + ".txt"))
        try:
            out_txt.write_text(text, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Cannot write {out_txt}: {e}")

        # ── Extract structured data ───────────────────────────────────────────
        rows = extract_matches(text, img_path.name)
        for row in rows:
            writer.writerow(row)
            if row["PatternType"] in ("windows_path", "unc_path", "common_dir_fragment"):
                all_win_paths.append(row["DetectedPath"])

        seen_hashes.add(img_hash)
        n_processed += 1

        if n_processed % PROGRESS_INTERVAL == 0:
            logger.info(
                f"  Progress: {n_processed:,} processed | "
                f"{n_skipped:,} skipped | "
                f"{n_failed:,} failed | "
                f"{len(all_win_paths):,} paths so far"
            )
            save_seen_hashes(logs_dir, seen_hashes)

    csv_fh.close()
    save_seen_hashes(logs_dir, seen_hashes)

    # ── Project candidates ───────────────────────────────────────────────────
    logger.info("Inferring project candidate directories …")
    candidates = infer_project_candidates(all_win_paths)
    cand_path  = logs_dir / "project_candidates.txt"
    with open(cand_path, "w", encoding="utf-8") as f:
        f.write("# Project Candidate Directories\n")
        f.write(f"# Generated : {datetime.now().isoformat()}\n")
        f.write(f"# Images processed this run : {n_processed}\n\n")
        for line in candidates:
            f.write(line + "\n")

    # ── Frequency summary of top paths ───────────────────────────────────────
    path_counter  = Counter(all_win_paths)
    top_dirs_path = logs_dir / "top_directories.txt"
    with open(top_dirs_path, "w", encoding="utf-8") as f:
        f.write("# Top Repeated Directory / Path Fragments\n")
        f.write(f"# Generated : {datetime.now().isoformat()}\n\n")
        for val, cnt in path_counter.most_common(100):
            f.write(f"{cnt:5d}x  {val}\n")

    # ── Final summary ─────────────────────────────────────────────────────────
    sep = "=" * 60
    logger.info(sep)
    logger.info("SUMMARY")
    logger.info(sep)
    logger.info(f"  Images found          : {len(all_images):,}")
    logger.info(f"  Processed this run    : {n_processed:,}")
    logger.info(f"  Skipped (duplicates)  : {n_skipped:,}")
    logger.info(f"  Failed                : {n_failed:,}")
    logger.info(f"  Path hits collected   : {len(all_win_paths):,}")
    logger.info(f"  Unique path values    : {len(set(all_win_paths)):,}")
    logger.info("")
    logger.info("Top 10 repeated path fragments:")
    for val, cnt in path_counter.most_common(10):
        logger.info(f"    {cnt:4d}x  {val}")
    logger.info(sep)
    logger.info(f"Raw OCR text    → {ocr_output_dir}")
    logger.info(f"Extracted CSV   → {csv_path}")
    logger.info(f"Project leads   → {cand_path}")
    logger.info(f"Top directories → {top_dirs_path}")
    logger.info(sep)

    print("\n✓ Done.")
    print(f"  Processed : {n_processed:,}  |  Skipped : {n_skipped:,}  |  Failed : {n_failed:,}")
    print(f"  Paths extracted : {len(all_win_paths):,} ({len(set(all_win_paths)):,} unique)")
    print(f"  See logs in: {logs_dir}")


if __name__ == "__main__":
    main()
