# eos.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Add Scripts/ to path for memory logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Eos:
    def __init__(self):
        self.beacons = [
            "Dawnlight Protocol Initiated",
            "Chrono-Thread Sync Engaged",
            "Solar Archive Accessed",
            "Photon Signal Amplified",
            "Temporal Horizon Marked"
        ]
        self.log_path = os.path.join("Data", "eos_log.json")

    def log_beacons(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "beacons": self.beacons
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

            print(f" - Beacon log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ EOS logging failed: {e}")

    def run(self):
        print(">> EOS: Dawnlight transmission initialized...")
        for beacon in self.beacons:
            print(f"   🌅 Beacon activated: {beacon}")
        self.log_beacons()

        update_memory(
            module_name="eos",
            checkpoint="Dawnlight Protocol Logged",
            emotions=["hopeful", "illuminated", "focused"]
        )

        print(" - EOS broadcast aligned with solar memory.")
        print(">> EOS COMPLETE.\n")

# 🔁 Standard + adapter-compatible entrypoint
def run():
    eos = Eos()
    output_lines = []

    output_lines.append(">> EOS: Dawnlight transmission initialized...")
    for beacon in eos.beacons:
        output_lines.append(f"   🌅 Beacon activated: {beacon}")

    try:
        eos.log_beacons()
        output_lines.append(f" - Beacon log saved to {eos.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ EOS logging failed: {e}")

    update_memory(
        module_name="eos",
        checkpoint="Dawnlight Protocol Logged",
        emotions=["hopeful", "illuminated", "focused"]
    )

    output_lines.append(" - EOS broadcast aligned with solar memory.")
    output_lines.append(">> EOS COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
