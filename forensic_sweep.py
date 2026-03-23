"""
FULL FORENSIC SWEEP — Master Data Consolidation Tool
=====================================================
Scans all data on C: and D: drives for:
  - Crypto wallets (addresses, private keys, seed phrases, mnemonics)
  - API keys and tokens (OpenAI, Infura, Alchemy, etc.)
  - SSH keys, PGP keys, KeePass databases
  - .env files, config files with secrets
  - Solidity contracts, deployment artifacts
  - Bot/agent config strings
  - Personal identity data (for ownership verification)
  - Duplicate files (by hash)

Outputs:
  - D:\DataVault\Organized\forensic_master_report.json  (full structured data)
  - D:\DataVault\Organized\forensic_master_report.md    (human-readable)
  - D:\DataVault\Organized\SENSITIVE_ITEMS.json         (vault candidates)
  - D:\DataVault\Organized\DUPLICATES.json              (exact dupes to clean)
"""

import os
import re
import json
import hashlib
import datetime
import sys
from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path(r"D:\DataVault\Organized")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Scan roots — everything that matters
SCAN_ROOTS = [
    r"C:\Users\natha",
    r"D:\DataVault",
    r"D:\KeePassXC_Review",
    r"D:\root",
    r"D:\The_Birth_of_a_Pantheon",
    r"D:\The_Birth_of_a_Pantheon_PhasePort",
    r"D:\FileHistory",
]

# Skip these — game installs, caches, node_modules, .git internals
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'site-packages', 'dist-packages', 'cache', 'Cache',
    'CachedData', 'CachedExtensions', 'CachedExtensionVSIXs',
    'Battlestate Games', 'Call of Duty', 'Call of Duty Modern Warfare',
    'Diablo II Resurrected', 'Overwatch', 'SteamLibrary', 'SPT',
    'Tom Clancy\'s Rainbow Six Siege', 'World of Warcraft', 'XboxGames',
    'WindowsApps', 'WpSystem', 'WUDownloadCache',
    'DXCache', 'GPUCache', 'ShaderCache', 'Code Cache',
    'D3DSCache', 'DawnGraphiteCache', 'DawnWebGPUCache',
    'Microsoft\\Edge', 'Google\\Chrome',
    'BraveSoftware', 'Package Cache',
    'pip', 'wheels',
}

# File extensions of interest
TEXT_EXTENSIONS = {
    '.txt', '.md', '.json', '.env', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.conf', '.config', '.properties', '.xml', '.csv', '.log',
    '.sol', '.js', '.ts', '.py', '.ps1', '.bat', '.cmd', '.sh',
    '.html', '.htm', '.key', '.pem', '.pub', '.asc', '.gpg',
    '.kdbx', '.kdb', '.keychain',
    '.bak', '.old', '.orig', '.backup',
}

# Binary extensions that might contain keys
BINARY_KEY_EXTENSIONS = {'.kdbx', '.kdb', '.p12', '.pfx', '.jks', '.keychain', '.wallet', '.dat'}

# Max file size to scan text content (10 MB)
MAX_TEXT_SIZE = 10 * 1024 * 1024

# ============================================================
# REGEX PATTERNS — What we're hunting
# ============================================================

PATTERNS = {
    # Crypto addresses
    "eth_address": re.compile(r'\b0x[0-9a-fA-F]{40}\b'),
    "btc_address": re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),
    "btc_bech32": re.compile(r'\bbc1[a-zA-HJ-NP-Z0-9]{25,90}\b'),
    
    # Private keys
    "eth_private_key": re.compile(r'\b[0-9a-fA-F]{64}\b'),
    "wif_private_key": re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
    
    # Seed / Mnemonic phrases: 12+ lowercase words in sequence (fast heuristic)
    "seed_phrase_candidate": re.compile(
        r'(?:[a-z]{3,10})(?: +(?:[a-z]{3,10})){11,23}',
        re.IGNORECASE
    ),

    # API keys
    "api_key_generic": re.compile(r'(?:api[_-]?key|apikey|api[_-]?secret|api[_-]?token)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', re.IGNORECASE),
    "openai_key": re.compile(r'sk-[A-Za-z0-9]{20,}'),
    "infura_key": re.compile(r'(?:infura|INFURA)[^=]*[:=]\s*["\']?([a-f0-9]{32})["\']?', re.IGNORECASE),
    "alchemy_key": re.compile(r'(?:alchemy|ALCHEMY)[^=]*[:=]\s*["\']?([A-Za-z0-9_-]{32,})["\']?', re.IGNORECASE),
    
    # Env var patterns
    "env_secret": re.compile(r'(?:PRIVATE_KEY|SECRET_KEY|MNEMONIC|SEED_PHRASE|PASSPHRASE|PASSWORD|METAMASK|WALLET)\s*=\s*(.+)', re.IGNORECASE),
    
    # SSH / PGP markers
    "ssh_private": re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    "pgp_private": re.compile(r'-----BEGIN PGP PRIVATE KEY BLOCK-----'),
    
    # Transaction hashes
    "tx_hash": re.compile(r'\b0x[0-9a-fA-F]{64}\b'),
    
    # Contract deployment markers
    "contract_deploy": re.compile(r'(?:deployed|contract|bytecode|abi|constructor|pragma solidity)', re.IGNORECASE),
    
    # KeePass / password manager
    "keepass_ref": re.compile(r'(?:keepass|\.kdbx|\.kdb|master.?password|database.?password)', re.IGNORECASE),
    
    # Bot / agent connection strings
    "bot_token": re.compile(r'(?:bot[_-]?token|discord[_-]?token|telegram[_-]?token)\s*[:=]\s*["\']?([A-Za-z0-9._\-]{30,})["\']?', re.IGNORECASE),
    "connection_string": re.compile(r'(?:mongodb|postgres|mysql|redis|amqp|wss?|https?)://[^\s"\'<>]{10,}', re.IGNORECASE),
}

# Filename patterns that are inherently interesting
INTERESTING_FILENAMES = re.compile(
    r'(?:wallet|seed|mnemonic|passphrase|private.?key|secret|\.env|\.kdbx|\.kdb|'
    r'keystore|credentials|vault|recovery|backup.*key|token.*config|'
    r'deploy|contract|solidity|hardhat|foundry|remix|'
    r'\.pem|\.p12|\.pfx|\.asc|id_rsa|id_ed25519|id_ecdsa|'
    r'password|passwd|auth|api.?key)',
    re.IGNORECASE
)

# ============================================================
# SCANNING ENGINE
# ============================================================

class ForensicScanner:
    def __init__(self):
        self.findings = defaultdict(list)  # category -> [finding]
        self.file_hashes = defaultdict(list)  # hash -> [paths]
        self.sensitive_items = []
        self.stats = {
            "files_scanned": 0,
            "dirs_scanned": 0,
            "dirs_skipped": 0,
            "text_files_read": 0,
            "matches_found": 0,
            "errors": 0,
        }
        self.interesting_files = []  # Files interesting by name alone
    
    def should_skip_dir(self, dirpath):
        name = os.path.basename(dirpath)
        # Skip known garbage
        if name in SKIP_DIRS:
            return True
        # Skip deeply nested game/app dirs
        if any(skip in dirpath for skip in [
            'Battlestate Games', 'Call of Duty', 'Diablo II',
            'Overwatch', 'SteamLibrary', 'Rainbow Six',
            'World of Warcraft', 'XboxGames', 'WindowsApps',
            'WpSystem', 'WUDownloadCache', 'SPT',
            'Microsoft\\Edge\\User Data', 'Google\\Chrome',
            'BraveSoftware', 'DXCache', 'GPUCache', 'ShaderCache',
        ]):
            return True
        return False
    
    def hash_file(self, filepath):
        """Get MD5 hash of file for deduplication."""
        try:
            h = hashlib.md5()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None
    
    def scan_text_file(self, filepath, size):
        """Scan a text file for pattern matches."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(min(size, MAX_TEXT_SIZE))
            
            if not content:
                return
            
            self.stats["text_files_read"] += 1
            
            for pattern_name, pattern in PATTERNS.items():
                matches = pattern.findall(content)
                if matches:
                    # Limit stored matches per file per pattern
                    unique_matches = list(set(matches[:50]))
                    for match in unique_matches:
                        match_str = match if isinstance(match, str) else str(match)
                        # Skip very short or very common hex strings (likely not keys)
                        if pattern_name == "eth_private_key" and len(match_str) == 64:
                            # Verify it's not just a hash in a random context
                            # Only flag if near wallet/key/private/secret context
                            ctx_start = max(0, content.find(match_str) - 100)
                            ctx_end = min(len(content), content.find(match_str) + 164)
                            context = content[ctx_start:ctx_end].lower()
                            if not any(kw in context for kw in ['key', 'private', 'secret', 'wallet', 'mnemonic', 'seed', 'account']):
                                continue
                        
                        finding = {
                            "file": filepath,
                            "pattern": pattern_name,
                            "match": match_str[:200],  # Truncate for safety
                            "size": size,
                        }
                        
                        # Mark sensitivity
                        if pattern_name in ("eth_private_key", "wif_private_key", "ssh_private",
                                          "pgp_private", "seed_phrase_candidate", "env_secret",
                                          "openai_key"):
                            finding["sensitivity"] = "CRITICAL"
                            self.sensitive_items.append(finding)
                        elif pattern_name in ("api_key_generic", "bot_token", "connection_string",
                                             "infura_key", "alchemy_key"):
                            finding["sensitivity"] = "HIGH"
                            self.sensitive_items.append(finding)
                        else:
                            finding["sensitivity"] = "NORMAL"
                        
                        self.findings[pattern_name].append(finding)
                        self.stats["matches_found"] += 1
                        
        except Exception as e:
            self.stats["errors"] += 1
    
    def scan_path(self, root_path):
        """Walk a directory tree and scan everything."""
        print(f"\n[SCANNING] {root_path}")
        
        if not os.path.exists(root_path):
            print(f"  SKIP: Path does not exist")
            return
        
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True, onerror=lambda e: None):
            # Filter out skip dirs IN PLACE (modifies walk behavior)
            try:
                dirnames[:] = [d for d in dirnames if not self.should_skip_dir(os.path.join(dirpath, d))]
            except Exception:
                continue
            
            self.stats["dirs_scanned"] += 1
            
            if self.stats["dirs_scanned"] % 500 == 0:
                print(f"  ... {self.stats['dirs_scanned']} dirs, {self.stats['files_scanned']} files, {self.stats['matches_found']} matches")
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                self.stats["files_scanned"] += 1
                
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    continue
                
                try:
                    ext = os.path.splitext(filename)[1].lower()
                    
                    # Check if filename itself is interesting
                    if INTERESTING_FILENAMES.search(filename):
                        self.interesting_files.append({
                            "file": filepath,
                            "size": size,
                            "ext": ext,
                        })
                    
                    # Hash files under 50MB for dedup
                    if size > 0 and size < 50 * 1024 * 1024:
                        if ext in TEXT_EXTENSIONS or ext in BINARY_KEY_EXTENSIONS or size < 1024 * 1024:
                            fhash = self.hash_file(filepath)
                            if fhash:
                                try:
                                    mtime = os.path.getmtime(filepath)
                                except OSError:
                                    mtime = 0
                                self.file_hashes[fhash].append({
                                    "path": filepath,
                                    "size": size,
                                    "mtime": mtime,
                                })
                    
                    # Scan text content
                    if ext in TEXT_EXTENSIONS and size > 0 and size < MAX_TEXT_SIZE:
                        self.scan_text_file(filepath, size)
                    
                    # Also scan extensionless files if small (often contain secrets)
                    elif ext == '' and size > 0 and size < 100000:
                        self.scan_text_file(filepath, size)
                    
                    # Note binary key files
                    if ext in BINARY_KEY_EXTENSIONS:
                        self.findings["binary_key_file"].append({
                            "file": filepath,
                            "pattern": "binary_key_file",
                            "match": f"Binary key file: {filename}",
                            "size": size,
                            "sensitivity": "HIGH",
                        })
                        self.sensitive_items.append(self.findings["binary_key_file"][-1])
                except Exception as e:
                    self.stats["errors"] += 1
    
    def find_duplicates(self):
        """Return files that have exact duplicates."""
        dupes = {}
        for fhash, entries in self.file_hashes.items():
            if len(entries) > 1:
                # Sort by mtime, oldest first (that's the "original")
                entries.sort(key=lambda x: x["mtime"])
                dupes[fhash] = {
                    "original": entries[0],
                    "duplicates": entries[1:],
                    "count": len(entries),
                    "wasted_bytes": sum(e["size"] for e in entries[1:]),
                }
        return dupes
    
    def generate_report(self):
        """Generate the master report."""
        duplicates = self.find_duplicates()
        
        report = {
            "timestamp": TIMESTAMP,
            "scan_date": datetime.datetime.now().isoformat(),
            "stats": self.stats,
            "scan_roots": SCAN_ROOTS,
            "findings_by_category": {},
            "interesting_files": self.interesting_files,
            "sensitive_items_count": len(self.sensitive_items),
            "duplicate_groups": len(duplicates),
            "total_wasted_by_dupes": sum(d["wasted_bytes"] for d in duplicates.values()),
        }
        
        for category, items in self.findings.items():
            report["findings_by_category"][category] = {
                "count": len(items),
                "items": items,
            }
        
        return report, duplicates
    
    def generate_markdown(self, report, duplicates):
        """Generate human-readable markdown report."""
        lines = []
        lines.append(f"# FORENSIC SWEEP — Master Report")
        lines.append(f"**Date:** {report['scan_date']}")
        lines.append(f"**Scan Roots:** {len(report['scan_roots'])} locations")
        lines.append("")
        
        lines.append("## Summary Stats")
        for k, v in report["stats"].items():
            lines.append(f"- **{k}:** {v:,}")
        lines.append(f"- **Sensitive items found:** {report['sensitive_items_count']}")
        lines.append(f"- **Duplicate groups:** {report['duplicate_groups']}")
        lines.append(f"- **Wasted space by dupes:** {report['total_wasted_by_dupes']:,} bytes")
        lines.append("")
        
        # Sensitive items (CRITICAL first)
        lines.append("## CRITICAL / HIGH Sensitivity Items")
        lines.append("*These need to go into the secure vault immediately.*\n")
        
        critical = [s for s in self.sensitive_items if s.get("sensitivity") == "CRITICAL"]
        high = [s for s in self.sensitive_items if s.get("sensitivity") == "HIGH"]
        
        if critical:
            lines.append("### CRITICAL")
            for item in critical:
                # REDACT the actual match value in the report
                lines.append(f"- **{item['pattern']}** in `{item['file']}`")
                lines.append(f"  - Match: `[REDACTED — {len(item.get('match',''))} chars]`")
        
        if high:
            lines.append("\n### HIGH")
            for item in high:
                lines.append(f"- **{item['pattern']}** in `{item['file']}`")
                lines.append(f"  - Match: `[REDACTED — {len(item.get('match',''))} chars]`")
        
        lines.append("")
        
        # Category breakdown
        lines.append("## Findings by Category")
        for category, data in sorted(report["findings_by_category"].items(), key=lambda x: -x[1]["count"]):
            lines.append(f"\n### {category} ({data['count']} hits)")
            # Show unique files
            unique_files = set(item["file"] for item in data["items"])
            for f in sorted(unique_files)[:30]:
                lines.append(f"- `{f}`")
            if len(unique_files) > 30:
                lines.append(f"- ... and {len(unique_files) - 30} more files")
        
        lines.append("")
        
        # Interesting files by name
        lines.append("## Interesting Files (by filename)")
        for item in sorted(self.interesting_files, key=lambda x: x["file"]):
            lines.append(f"- `{item['file']}` ({item['size']:,} bytes)")
        
        lines.append("")
        
        # Duplicates
        lines.append("## Exact Duplicates")
        lines.append(f"*{len(duplicates)} groups of duplicate files found.*\n")
        
        for fhash, info in sorted(duplicates.items(), key=lambda x: -x[1]["wasted_bytes"])[:100]:
            lines.append(f"**Hash:** `{fhash}` — {info['count']} copies, {info['wasted_bytes']:,} bytes wasted")
            lines.append(f"  - KEEP (original): `{info['original']['path']}`")
            for d in info["duplicates"]:
                lines.append(f"  - DELETE: `{d['path']}`")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("FULL FORENSIC SWEEP — Starting")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Scanning {len(SCAN_ROOTS)} roots...")
    print("=" * 60)
    
    scanner = ForensicScanner()
    
    for root in SCAN_ROOTS:
        scanner.scan_path(root)
    
    print(f"\n{'='*60}")
    print("SCAN COMPLETE — Generating reports...")
    print(f"  Files: {scanner.stats['files_scanned']:,}")
    print(f"  Matches: {scanner.stats['matches_found']:,}")
    print(f"  Sensitive: {len(scanner.sensitive_items)}")
    
    report, duplicates = scanner.generate_report()
    
    # Save JSON report
    json_path = OUTPUT_DIR / f"forensic_master_report_{TIMESTAMP}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  JSON: {json_path}")
    
    # Save markdown report
    md_path = OUTPUT_DIR / f"forensic_master_report_{TIMESTAMP}.md"
    md_content = scanner.generate_markdown(report, duplicates)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"  Markdown: {md_path}")
    
    # Save sensitive items separately
    sens_path = OUTPUT_DIR / f"SENSITIVE_ITEMS_{TIMESTAMP}.json"
    with open(sens_path, 'w', encoding='utf-8') as f:
        json.dump(scanner.sensitive_items, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Sensitive: {sens_path}")
    
    # Save duplicates
    dupes_path = OUTPUT_DIR / f"DUPLICATES_{TIMESTAMP}.json"
    with open(dupes_path, 'w', encoding='utf-8') as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Duplicates: {dupes_path}")
    
    # Also save a latest symlink-style copy
    for name, src in [
        ("forensic_master_report.json", json_path),
        ("forensic_master_report.md", md_path),
        ("SENSITIVE_ITEMS.json", sens_path),
        ("DUPLICATES.json", dupes_path),
    ]:
        dest = OUTPUT_DIR / name
        import shutil
        shutil.copy2(src, dest)
    
    print(f"\n{'='*60}")
    print("DONE. Reports in D:\\DataVault\\Organized\\")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
