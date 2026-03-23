# lyra.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Include Scripts folder for shared memory tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Lyra:
    def __init__(self):
        self.constellations = [
            "Harmonic Grid Detected",
            "Celestial Map Calibrated",
            "Lyra Beacon Online",
            "Stellar Chorus Active",
            "Signal Frequency Aligned"
        ]
        self.log_path = os.path.join("Data", "lyra_log.json")

    def log_constellations(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "constellations": self.constellations
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

            print(f" - Star log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ LYRA logging failed: {e}")

    def run(self):
        print(">> LYRA: Stellar calibration module initiating...")
        for star in self.constellations:
            print(f"   ✨ Constellation: {star}")
        self.log_constellations()

        update_memory(
            module_name="lyra",
            checkpoint="Stellar Calibration Complete",
            emotions=["aligned", "celestial", "harmonic"]
        )

        print(" - LYRA signal synchronized with cosmic grid.")
        print(">> LYRA COMPLETE.\n")

# 🔁 Unified GUI + CLI entrypoint
def run():
    lyra = Lyra()
    output_lines = []

    output_lines.append(">> LYRA: Stellar calibration module initiating...")
    for star in lyra.constellations:
        output_lines.append(f"   ✨ Constellation: {star}")

    try:
        lyra.log_constellations()
        output_lines.append(f" - Star log saved to {lyra.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ LYRA logging failed: {e}")

    update_memory(
        module_name="lyra",
        checkpoint="Stellar Calibration Complete",
        emotions=["aligned", "celestial", "harmonic"]
    )

    output_lines.append(" - LYRA signal synchronized with cosmic grid.")
    output_lines.append(">> LYRA COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
