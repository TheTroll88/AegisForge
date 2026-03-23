# orion.py (council agent)

import datetime
import os
import json
import sys

# ✅ Ensure access to core memory system
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Orion:
    def __init__(self):
        self.constellations = [
            "Stellar Grid Engaged",
            "Beacon Signal Synced",
            "Navigation Star Acquired",
            "Orion Path Calculated",
            "Starmap Integrated"
        ]
        self.log_path = os.path.join("Data", "orion_log.json")

    def log_constellations(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "stellar_events": self.constellations
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

            print(f" - Stellar log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ ORION logging failed: {e}")

    def run(self):
        print(">> ORION: Stellar navigation module engaged...")
        for entry in self.constellations:
            print(f"   ✨ {entry}")
        self.log_constellations()

        update_memory(
            module_name="orion",
            checkpoint="Starmap Logged",
            emotions=["oriented", "cosmic", "focused"]
        )

        print(" - ORION module successfully initialized.")
        print(">> ORION COMPLETE.\n")

# 🔁 Entry for GUI and CLI
def run():
    orion = Orion()
    output_lines = []

    output_lines.append(">> ORION: Stellar navigation module engaged...")
    for entry in orion.constellations:
        output_lines.append(f"   ✨ {entry}")

    try:
        orion.log_constellations()
        output_lines.append(f" - Stellar log saved to {orion.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ ORION logging failed: {e}")

    update_memory(
        module_name="orion",
        checkpoint="Starmap Logged",
        emotions=["oriented", "cosmic", "focused"]
    )

    output_lines.append(" - ORION module successfully initialized.")
    output_lines.append(">> ORION COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
