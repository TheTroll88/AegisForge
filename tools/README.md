# Tools

Standalone open-source utilities. These are personal productivity tools, **not part of the AegisForge trading app**. Each is MIT-licensed and works independently.

## auto_organizer.py

File sorting daemon. Watches a dropbox folder and auto-sorts files into 12 categories by extension, with MD5 dedup (duplicates are deleted, not moved).

**Setup:** Paths default to `~/DataVault/Dropbox` (input) and `~/DataVault/Organized` (output). Override with `ORGANIZER_DROPBOX_DIR` and `ORGANIZER_OUTPUT_DIR` environment variables.

**Troubleshooting:**

| Problem | Fix |
|---------|-----|
| Script exits immediately | The dropbox or output directory doesn't exist. Create them first. |
| Files aren't moving | Check write permissions on the output folder and that the daemon is actually running (check PID file in `%TEMP%`). |
| Duplicate deleted a file I wanted | Dedup is by content hash. If the same file exists in the destination, the incoming copy is removed. Keep originals elsewhere if unsure. |
| `.env` file sorted as "Config" | By design. Be careful not to drop live wallet `.env` files into the dropbox — they contain secrets. |

---

## manage_organizer.ps1

Start/stop/status controller for auto_organizer. Can install as a Windows Scheduled Task.

---

## ocr_pipeline.py

Extracts text from screenshots using Tesseract OCR. Finds Windows paths, filenames, URLs, terminal commands, and project indicators.

**Requirements:** Tesseract 5.x installed, plus `pytesseract`, `Pillow`, `opencv-python-headless`, `numpy`.

**Troubleshooting:**

| Problem | Fix |
|---------|-----|
| "tesseract is not installed" | Install Tesseract and make sure the path in `TESSERACT_CMD` matches your install location. |
| Poor OCR accuracy | Dark-mode screenshots and low-res images produce worse results. The OpenCV preprocessor helps, but some images are just too noisy. |
| Want to reprocess old images | Delete or rename `processed_hashes.json` — it's the dedup cache. |
| CSV looks corrupt | If you kill the script mid-run, the last CSV row may be partial. Delete the last line and rerun. |

---

## forensic_sweep.py

Full-drive security scanner. Finds exposed secrets, private keys, seed phrases, credentials, and sensitive files.

**Troubleshooting:**

| Problem | Fix |
|---------|-----|
| False positives on seed phrases | The detector is heuristic (12+ lowercase words in a row). Book excerpts and code comments trigger it. Review results manually. |
| Large files missed | Text files over 10 MB are truncated. Secrets near the end of huge logs won't be caught. |
| "Permission denied" on some folders | Expected on system-protected directories. The scanner skips them silently and continues. |
| Old reports piling up | Reports are timestamped and never auto-deleted. Clean up old ones manually from the output folder. |
| Private key not flagged | The scanner only flags 64-hex strings near context words like "key" or "private". Isolated hex strings are intentionally skipped to reduce noise. |
