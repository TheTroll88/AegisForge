# nyx.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Access to PhasePort scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Nyx:
    def __init__(self):
        self.events = [
            "Dreamstate Linked",
            "Night Protocol Engaged",
            "Veil of Memory Lifted",
            "NYX Path Activated",
            "Subconscious Stream Online"
        ]
        self.log_path = os.path.join("Data", "nyx_log.json")

    def log_dreams(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "dream_events": self.events
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

            print(f" - Dream log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ NYX logging failed: {e}")

    def run(self):
        print(">> NYX: Dreamwalker sequence initiated...")
        for event in self.events:
            print(f"   🌒 Dream event: {event}")
        self.log_dreams()

        update_memory(
            module_name="nyx",
            checkpoint="Dream Sequence Completed",
            emotions=["dreamlike", "mysterious", "serene"]
        )

        print(" - NYX dreamlink established.")
        print(">> NYX COMPLETE.\n")

# 🔁 Entry for GUI and CLI
def run():
    nyx = Nyx()
    output_lines = []

    output_lines.append(">> NYX: Dreamwalker sequence initiated...")
    for event in nyx.events:
        output_lines.append(f"   🌒 Dream event: {event}")

    try:
        nyx.log_dreams()
        output_lines.append(f" - Dream log saved to {nyx.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ NYX logging failed: {e}")

    update_memory(
        module_name="nyx",
        checkpoint="Dream Sequence Completed",
        emotions=["dreamlike", "mysterious", "serene"]
    )

    output_lines.append(" - NYX dreamlink established.")
    output_lines.append(">> NYX COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
