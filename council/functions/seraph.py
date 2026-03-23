# seraph.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Add path to access shared memory module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory  # Unified memory logging system

class Seraph:
    def __init__(self):
        self.signals = [
            "Divine Firewall Activated",
            "Celestial Pulse Detected",
            "Wings of Flame Engaged",
            "Sanctum Access Verified",
            "Guardian Protocol Online"
        ]
        self.log_path = os.path.join("Data", "seraph_log.json")

    def log_signals(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "divine_events": self.signals
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

            print(f" - Divine signal log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ SERAPH logging failed: {e}")

    def run(self):
        print(">> SERAPH: Guardian oversight system initializing...")
        for signal in self.signals:
            print(f"   🔥 {signal}")
        self.log_signals()

        update_memory(
            module_name="seraph",
            checkpoint="Celestial Oversight Confirmed",
            emotions=["protected", "divine", "aware"]
        )

        print(" - SERAPH module guardian link established.")
        print(">> SERAPH COMPLETE.\n")

# 🔁 Entry for CLI and GUI
def run():
    seraph = Seraph()
    output_lines = []

    output_lines.append(">> SERAPH: Guardian oversight system initializing...")
    for signal in seraph.signals:
        output_lines.append(f"   🔥 {signal}")

    try:
        seraph.log_signals()
        output_lines.append(f" - Divine signal log saved to {seraph.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ SERAPH logging failed: {e}")

    update_memory(
        module_name="seraph",
        checkpoint="Celestial Oversight Confirmed",
        emotions=["protected", "divine", "aware"]
    )

    output_lines.append(" - SERAPH module guardian link established.")
    output_lines.append(">> SERAPH COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
