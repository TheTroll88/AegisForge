#!/usr/bin/env python3
"""Aegis Terminal Integration script for Bridge project.

Usage:
  python3 bridge_project/aegis_terminal.py

Command examples:
  aegis status
  aegis startup
  run ls -la
  help
  exit
"""
import os
import sys
import subprocess
from datetime import datetime

BRIDGE_ROOT = os.environ.get("BRIDGE_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
LOG_PATH = os.path.join(BRIDGE_ROOT, "bridge_project", "logs", "aegis_terminal.log")
SESSION_LOG_PATH = os.path.join(BRIDGE_ROOT, "bridge_project", "logs", "ghost_replay.log")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)


def log(msg: str):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    with open(SESSION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)

def replay_log(msg: str):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}\n"
    with open(SESSION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def run_shell(cmd: str):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        return f"Command failed with code {e.returncode}: {e.output.strip()}"


def print_banner():
    print("Aegis Terminal Integration is running. Type your commands below:")
    print("Type 'help' for available commands. Type 'exit' to quit.")


def print_help():
    print("Aegis Terminal Commands:")
    print("  help                     Show this help message")
    print("  status                   Print Bridge and Aegis status")
    print("  startup                  Run the Bridge startup script")
    print("  log                      Show last 20 lines from Aegis log")
    print("  run <shell command>      Execute shell command")
    print("  aegis <subcommand>       Aegis action (e.g. aegis status)")
    print("  exit                     Quit Aegis terminal")


def show_status():
    print("Aegis Terminal Status:")
    print(f"  Bridge root: {BRIDGE_ROOT}")
    print(f"  Log path: {LOG_PATH}")
    print("  Aegis: online")


def show_log():
    if not os.path.exists(LOG_PATH):
        print("No Aegis log yet.")
        return
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()[-20:]
    print("--- Aegis Log (last 20 lines) ---")
    for l in lines:
        print(l.rstrip())


def run_startup_script():
    startup_script = os.path.join(BRIDGE_ROOT, "bridge_project", "scripts", "startup.sh")
    if not os.path.exists(startup_script):
        print(f"Startup script not found: {startup_script}")
        return
    result = run_shell(f"bash {startup_script}")
    print(result)


def main():
    print_banner()
    log("Aegis terminal started")
    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            print("\nReceived EOF. Exiting.")
            break
        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Exiting.")
            break

        if not raw:
            continue

        command = raw.strip()
        log(f"USER: {command}")
        replay_log(f"USER: {command}")

        lower = command.lower()
        if lower in ["exit", "quit"]:
            print("Exiting Aegis Terminal.")
            log("Aegis terminal exited")
            break
        if lower in ["help", "?", "commands"]:
            print_help()
            continue
        if lower == "status":
            show_status()
            continue
        if lower == "startup":
            run_startup_script()
            replay_log("Aegis: ran startup")
            continue
        if lower == "log":
            show_log()
            replay_log("Aegis: showed log")
            continue
        if lower.startswith("aegis"):
            print("Aegis command received. Bridge is monitoring.")
            replay_log(f"Aegis: {command}")
            continue
        if lower.startswith("run "):
            cmd = command[4:].strip()
            out = run_shell(cmd)
            print(out)
            log(f"SHELL: {cmd} -> {out[:200]}")
            replay_log(f"SHELL: {cmd} -> {out[:200]}")
            continue

        print("Unknown command. Type 'help' for commands.")


if __name__ == "__main__":
    main()
