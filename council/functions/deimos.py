# deimos.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Import shared memory logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Deimos:
    def __init__(self):
        self.signals = ["Shadow Pulse", "Wraith Echo", "Dissonant Field", "Void Crackle", "Fear Harmonics"]
        self.log_path = os.path.join("Data", "deimos_log.json")

    def log_signals(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "signals_detected": self.signals
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

            print(f" - Signal log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ DEIMOS logging failed: {e}")

    def run(self):
        print(">> DEIMOS: Shadow telemetry activated...")
        for signal in self.signals:
            print(f"   ⚡ Signal registered: {signal}")
        self.log_signals()

        update_memory(
            module_name="deimos",
            checkpoint="Dark Signal Matrix Sync",
            emotions=["ominous", "intense", "calculated"]
        )

        print(" - DEIMOS channel established.")
        print(">> DEIMOS COMPLETE.\n")

# 🔁 GUI-compatible + CLI-compatible entrypoint
def run():
    deimos = Deimos()
    output_lines = []

    output_lines.append(">> DEIMOS: Shadow telemetry activated...")
    for signal in deimos.signals:
        output_lines.append(f"   ⚡ Signal registered: {signal}")

    try:
        deimos.log_signals()
        output_lines.append(f" - Signal log saved to {deimos.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ DEIMOS logging failed: {e}")

    update_memory(
        module_name="deimos",
        checkpoint="Dark Signal Matrix Sync",
        emotions=["ominous", "intense", "calculated"]
    )

    output_lines.append(" - DEIMOS channel established.")
    output_lines.append(">> DEIMOS COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
