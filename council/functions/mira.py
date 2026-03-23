# mira.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Ensure access to shared tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Mira:
    def __init__(self):
        self.signs = [
            "Reflective Memory Unlocked",
            "Mirror Sync Achieved",
            "Symbolic Echo Detected",
            "MIRA Channel Open",
            "Soul Reflection Online"
        ]
        self.log_path = os.path.join("Data", "mira_log.json")

    def log_symbols(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "symbols": self.signs
        }

        os.makedirs("Data", exist_ok=True)
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)
            with open(self.log_path, 'w') as f:
                json.dump(logs, f, indent=4)

            print(f" - Symbolic log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ MIRA logging failed: {e}")

    def run(self):
        print(">> MIRA: Reflection protocol initiating...")
        for sign in self.signs:
            print(f"   🪞 Reflection: {sign}")
        self.log_symbols()

        update_memory(
            module_name="mira",
            checkpoint="Symbolic Reflection Complete",
            emotions=["reflective", "synced", "introspective"]
        )

        print(" - MIRA synchronization established.")
        print(">> MIRA COMPLETE.\n")

# 🔁 Unified entrypoint for GUI and CLI
def run():
    mira = Mira()
    output_lines = []

    output_lines.append(">> MIRA: Reflection protocol initiating...")
    for sign in mira.signs:
        output_lines.append(f"   🪞 Reflection: {sign}")

    try:
        mira.log_symbols()
        output_lines.append(f" - Symbolic log saved to {mira.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ MIRA logging failed: {e}")

    update_memory(
        module_name="mira",
        checkpoint="Symbolic Reflection Complete",
        emotions=["reflective", "synced", "introspective"]
    )

    output_lines.append(" - MIRA synchronization established.")
    output_lines.append(">> MIRA COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
