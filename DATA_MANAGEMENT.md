# LITCOIN Miner — Data Management System

## Overview

This workspace contains tools for forensic data gathering, automatic file organization, and secure credential management.

## Quick Start

```powershell
# Run a one-time sort of the Dropbox
.\manage_organizer.ps1 -Action once

# Start the background daemon (auto-sorts files continuously)
.\manage_organizer.ps1 -Action start

# Check daemon status
.\manage_organizer.ps1 -Action status

# Stop daemon
.\manage_organizer.ps1 -Action stop

# Install to run at login (scheduled task)
.\manage_organizer.ps1 -Action install
```

## Directory Layout

```
D:\DataVault\
  Dropbox\         <-- DROP FILES HERE, they get auto-sorted
  Organized\       <-- Clean category-based storage
    Code/          .py, .js, .ts, .sol, .rs, .go, etc.
    Config/        .env, .json, .yaml, .toml, .ini
    Crypto/        .sol, .abi, .kdbx, wallet files
    Documents/     .md, .txt, .pdf, .doc
    Images/        .png, .jpg, .gif, .svg
    Keys/          .pem, .p12, .pfx, private keys
    Logs/          .log files
    Scripts/       .ps1, .bat, .sh
    Data/          .db, .sqlite, .csv, .xlsx
    Archives/      .zip, .tar, .7z, .rar
    Media/         .mp3, .mp4, .wav
    Other/         everything else
  Logs\            Daemon and scan logs
  Screenshots\     Source screenshots for OCR
  OCR_Output\      OCR results
```

## Tools

### forensic_sweep.py
Full-system forensic scanner. Scans C: and D: drives for crypto, keys, secrets, credentials, contracts. Finds duplicates and categorizes sensitivity.

```powershell
python forensic_sweep.py
```

Output goes to `D:\DataVault\Organized\`:
- `forensic_master_report.json` — Full structured data
- `forensic_master_report.md` — Human-readable report
- `SENSITIVE_ITEMS.json` — Items needing vault protection
- `DUPLICATES.json` — Exact duplicates to clean up

### auto_organizer.py
The file sorting daemon. Watches `D:\DataVault\Dropbox\` and routes files to organized categories.

```powershell
python auto_organizer.py        # Start daemon
python auto_organizer.py once   # Single pass
python auto_organizer.py status # Check running
python auto_organizer.py stop   # Stop daemon
```

### manage_organizer.ps1
PowerShell wrapper for the daemon with scheduled task support.

### secure_vault.ps1
Windows DPAPI-based secret storage for sensitive credentials found by the scanner.

```powershell
.\secure_vault.ps1 set my_secret "value"
.\secure_vault.ps1 get my_secret
.\secure_vault.ps1 status
```

### ocr_pipeline.py
Screenshot OCR extraction. Processes images from `D:\DataVault\Screenshots\` and extracts text/paths/data.
