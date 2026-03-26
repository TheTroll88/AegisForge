"""
AUTO-ORGANIZER DAEMON
=====================
Watches a Dropbox intake folder and automatically sorts files
into a clean category-based directory structure.

Features:
- Watches ORGANIZER_DROPBOX_DIR for new files (default: ~/DataVault/Dropbox)
- Routes files to categories based on extension and content
- Deduplicates by MD5 hash (skips if already exists)
- Logs all actions
- Runs as a background daemon via scheduled task or manual start

Categories:
  Code/        - .py, .js, .ts, .sol, .rs, .go, .c, .cpp, .java, .rb
  Config/      - .env, .json, .yaml, .yml, .toml, .ini, .cfg, .conf
  Crypto/      - .sol, .abi, wallet files, keystore, .kdbx
  Documents/   - .md, .txt, .pdf, .doc, .docx, .rtf, .csv
  Images/      - .png, .jpg, .jpeg, .gif, .svg, .bmp, .webp, .ico
  Keys/        - .pem, .p12, .pfx, .asc, .key, id_rsa, id_ed25519
  Logs/        - .log files
  Scripts/     - .ps1, .bat, .cmd, .sh, .bash
  Data/        - .db, .sqlite, .sql, .csv, .xlsx
  Archives/    - .zip, .tar, .gz, .7z, .rar, .bak
  Media/       - .mp3, .mp4, .wav, .avi, .mkv, .mov
  Other/       - anything else

Configure directories via environment variables:
  ORGANIZER_DROPBOX_DIR  - intake folder (default: ~/DataVault/Dropbox)
  ORGANIZER_OUTPUT_DIR   - organized output (default: ~/DataVault/Organized)
  ORGANIZER_LOG_DIR      - log directory (default: ~/DataVault/Logs)
"""

import os
import sys
import time
import shutil
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

DROPBOX_DIR = Path(os.environ.get("ORGANIZER_DROPBOX_DIR", str(Path.home() / "DataVault" / "Dropbox")))
ORGANIZED_DIR = Path(os.environ.get("ORGANIZER_OUTPUT_DIR", str(Path.home() / "DataVault" / "Organized")))
LOG_DIR = Path(os.environ.get("ORGANIZER_LOG_DIR", str(Path.home() / "DataVault" / "Logs")))
PID_FILE = Path(os.environ.get("TEMP", str(Path.home() / "AppData" / "Local" / "Temp"))) / "auto_organizer.pid"
POLL_INTERVAL = 5  # seconds between checks

# Category routing by extension
CATEGORY_MAP = {
    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".tsx": "Code", ".jsx": "Code",
    ".sol": "Crypto", ".rs": "Code", ".go": "Code", ".c": "Code", ".cpp": "Code",
    ".h": "Code", ".java": "Code", ".rb": "Code", ".php": "Code", ".swift": "Code",
    ".kt": "Code", ".cs": "Code", ".vue": "Code", ".svelte": "Code",
    # Config
    ".env": "Config", ".json": "Config", ".yaml": "Config", ".yml": "Config",
    ".toml": "Config", ".ini": "Config", ".cfg": "Config", ".conf": "Config",
    ".xml": "Config", ".properties": "Config",
    # Documents
    ".md": "Documents", ".txt": "Documents", ".pdf": "Documents",
    ".doc": "Documents", ".docx": "Documents", ".rtf": "Documents",
    ".odt": "Documents", ".tex": "Documents", ".rst": "Documents",
    # Images
    ".png": "Images", ".jpg": "Images", ".jpeg": "Images", ".gif": "Images",
    ".svg": "Images", ".bmp": "Images", ".webp": "Images", ".ico": "Images",
    ".tiff": "Images", ".tif": "Images", ".psd": "Images",
    # Keys / secrets
    ".pem": "Keys", ".p12": "Keys", ".pfx": "Keys", ".asc": "Keys",
    ".key": "Keys", ".pub": "Keys", ".ppk": "Keys",
    # Logs
    ".log": "Logs",
    # Scripts
    ".ps1": "Scripts", ".bat": "Scripts", ".cmd": "Scripts",
    ".sh": "Scripts", ".bash": "Scripts",
    # Data
    ".db": "Data", ".sqlite": "Data", ".sql": "Data",
    ".csv": "Data", ".xlsx": "Data", ".xls": "Data", ".tsv": "Data",
    # Archives
    ".zip": "Archives", ".tar": "Archives", ".gz": "Archives",
    ".7z": "Archives", ".rar": "Archives", ".bak": "Archives",
    ".tgz": "Archives", ".bz2": "Archives",
    # Media
    ".mp3": "Media", ".mp4": "Media", ".wav": "Media", ".flac": "Media",
    ".avi": "Media", ".mkv": "Media", ".mov": "Media", ".wmv": "Media",
    ".ogg": "Media", ".m4a": "Media",
    # Crypto-specific
    ".abi": "Crypto", ".kdbx": "Crypto", ".kdb": "Crypto",
}

# Filename patterns that override extension-based routing
FILENAME_OVERRIDES = {
    "wallet": "Crypto",
    "keystore": "Crypto",
    "mnemonic": "Crypto",
    "seed": "Crypto",
    "private_key": "Keys",
    "id_rsa": "Keys",
    "id_ed25519": "Keys",
    "id_ecdsa": "Keys",
    ".env": "Config",
}

# ============================================================
# SETUP
# ============================================================

def setup_dirs():
    """Create all necessary directories."""
    for d in [DROPBOX_DIR, ORGANIZED_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Create category subdirs
    categories = set(CATEGORY_MAP.values()) | {"Other"}
    for cat in categories:
        (ORGANIZED_DIR / cat).mkdir(exist_ok=True)


def setup_logging():
    """Configure logging."""
    log_file = LOG_DIR / f"auto_organizer_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("auto_organizer")


# ============================================================
# CORE LOGIC
# ============================================================

def md5_hash(filepath):
    """Get MD5 hash of a file."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def categorize_file(filepath):
    """Determine which category a file belongs to."""
    name = filepath.name.lower()
    ext = filepath.suffix.lower()
    
    # Check filename overrides first
    for pattern, category in FILENAME_OVERRIDES.items():
        if pattern in name:
            return category
    
    # Then check extension
    return CATEGORY_MAP.get(ext, "Other")


def file_exists_in_organized(filepath, category):
    """Check if an identical file already exists in the target category."""
    target_dir = ORGANIZED_DIR / category
    target_path = target_dir / filepath.name
    
    if not target_path.exists():
        return False
    
    # Same name exists - check if content matches
    try:
        return md5_hash(filepath) == md5_hash(target_path)
    except Exception:
        return False


def find_unique_name(target_dir, filename):
    """If filename exists, add a numeric suffix."""
    target = target_dir / filename
    if not target.exists():
        return target
    
    stem = Path(filename).stem
    ext = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{ext}"
        target = target_dir / new_name
        if not target.exists():
            return target
        counter += 1
        if counter > 1000:
            # Safety valve
            return target_dir / f"{stem}_{int(time.time())}{ext}"


def process_file(filepath, logger):
    """Process a single file from the dropbox."""
    try:
        if not filepath.is_file():
            return
        
        # Skip hidden/system files
        if filepath.name.startswith(".") or filepath.name.startswith("~"):
            return
        
        category = categorize_file(filepath)
        target_dir = ORGANIZED_DIR / category
        target_dir.mkdir(exist_ok=True)
        
        # Check for duplicates
        if file_exists_in_organized(filepath, category):
            logger.info(f"SKIP (duplicate): {filepath.name} -> {category}/")
            filepath.unlink()  # Remove the duplicate from dropbox
            return
        
        # Find unique name and move
        target_path = find_unique_name(target_dir, filepath.name)
        shutil.move(str(filepath), str(target_path))
        logger.info(f"SORTED: {filepath.name} -> {category}/{target_path.name}")
        
    except PermissionError:
        logger.warning(f"LOCKED: {filepath.name} (in use, will retry)")
    except Exception as e:
        logger.error(f"ERROR processing {filepath.name}: {e}")


def process_dropbox(logger):
    """Scan dropbox and process all files."""
    if not DROPBOX_DIR.exists():
        return 0
    
    count = 0
    for item in DROPBOX_DIR.iterdir():
        if item.is_file():
            process_file(item, logger)
            count += 1
        elif item.is_dir():
            # Process subdirectories recursively
            for sub_item in item.rglob("*"):
                if sub_item.is_file():
                    process_file(sub_item, logger)
                    count += 1
            # Remove empty dirs after processing
            try:
                if item.exists() and not any(item.iterdir()):
                    item.rmdir()
                    logger.info(f"CLEANED: empty dir {item.name}/")
            except Exception:
                pass
    
    return count


# ============================================================
# DAEMON
# ============================================================

def write_pid():
    """Write PID file for daemon management."""
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid():
    """Remove PID file on shutdown."""
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def run_daemon():
    """Main daemon loop."""
    setup_dirs()
    logger = setup_logging()
    write_pid()
    
    logger.info("=" * 50)
    logger.info("AUTO-ORGANIZER DAEMON STARTED")
    logger.info(f"Watching: {DROPBOX_DIR}")
    logger.info(f"Sorting to: {ORGANIZED_DIR}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info("=" * 50)
    
    try:
        while True:
            try:
                count = process_dropbox(logger)
                if count > 0:
                    logger.info(f"Processed {count} items this cycle")
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    finally:
        cleanup_pid()
        logger.info("AUTO-ORGANIZER DAEMON STOPPED")


def run_once():
    """Process dropbox once and exit."""
    setup_dirs()
    logger = setup_logging()
    logger.info("Running single pass...")
    count = process_dropbox(logger)
    logger.info(f"Done. Processed {count} items.")


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "once":
            run_once()
        elif cmd == "status":
            if PID_FILE.exists():
                pid = PID_FILE.read_text().strip()
                print(f"Daemon running (PID {pid})")
            else:
                print("Daemon not running")
        elif cmd == "stop":
            if PID_FILE.exists():
                pid = int(PID_FILE.read_text().strip())
                import signal
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"Sent stop signal to PID {pid}")
                except ProcessLookupError:
                    print("Daemon not running (stale PID file)")
                    PID_FILE.unlink(missing_ok=True)
            else:
                print("Daemon not running")
        else:
            print(f"Usage: {sys.argv[0]} [once|status|stop]")
            print("  (no args) = start daemon")
            print("  once      = process dropbox once and exit")
            print("  status    = check if daemon is running")
            print("  stop      = stop running daemon")
    else:
        run_daemon()


if __name__ == "__main__":
    main()
