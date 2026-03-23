# vira.py (council agent)

import datetime
import os
import json
import sys

# ✅ Ensure the Scripts/ directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory  # Unified memory system

class Vira:
    def __init__(self):
        self.events = [
            "Vital Core Online",
            "BioResonance Synced",
            "Heartbeat Pattern Detected",
            "Essence Flow Confirmed",
            "VIRA Node Linked"
        ]
        self.log_path = os.path.join("Data", "vira_log.json")

    def log_events(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "bio_events": self.events
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

            print(f" - VIRA log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ VIRA logging failed: {e}")

    def run(self):
        print(">> VIRA: Bio-intelligence module activated...")
        for event in self.events:
            print(f"   💓 {event}")
        self.log_events()

        update_memory(
            module_name="vira",
            checkpoint="BioStream Sync Complete",
            emotions=["vital", "aware", "synced"]
        )

        print(" - VIRA node successfully linked to vitality stream.")
        print(">> VIRA COMPLETE.\n")

# 🔁 Entry for both CLI and GUI usage
def run():
    vira = Vira()
    output_lines = []

    output_lines.append(">> VIRA: Bio-intelligence module activated...")
    for event in vira.events:
        output_lines.append(f"   💓 {event}")

    try:
        vira.log_events()
        output_lines.append(f" - VIRA log saved to {vira.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ VIRA logging failed: {e}")

    update_memory(
        module_name="vira",
        checkpoint="BioStream Sync Complete",
        emotions=["vital", "aware", "synced"]
    )

    output_lines.append(" - VIRA node successfully linked to vitality stream.")
    output_lines.append(">> VIRA COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
