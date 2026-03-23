# ciel.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Add unified memory logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Ciel:
    def __init__(self):
        self.elements = ["Air", "Cloud", "Stratos", "Pulse", "Nimbus"]
        self.log_path = os.path.join("Data", "ciel_log.json")

    def log_elements(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "elements_logged": self.elements
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

            print(f" - Element log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ CIEL logging failed: {e}")

    def run(self):
        print(">> CIEL: Sky-bound telemetry interface engaged...")
        for element in self.elements:
            print(f"   ☁ Element linked: {element}")
        self.log_elements()

        update_memory(
            module_name="ciel",
            checkpoint="Atmospheric Linkage Complete",
            emotions=["elevated", "transcendent", "clear"]
        )

        print(" - CIEL atmospheric uplink confirmed.")
        print(">> CIEL COMPLETE.\n")

# 🔁 Standalone + adapter-compatible entrypoint
def run():
    ciel = Ciel()
    output_lines = []

    output_lines.append(">> CIEL: Sky-bound telemetry interface engaged...")
    for element in ciel.elements:
        output_lines.append(f"   ☁ Element linked: {element}")

    try:
        ciel.log_elements()
        output_lines.append(f" - Element log saved to {ciel.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ CIEL logging failed: {e}")

    update_memory(
        module_name="ciel",
        checkpoint="Atmospheric Linkage Complete",
        emotions=["elevated", "transcendent", "clear"]
    )

    output_lines.append(" - CIEL atmospheric uplink confirmed.")
    output_lines.append(">> CIEL COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
