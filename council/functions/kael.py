# kael.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Add Scripts/ directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Kael:
    def __init__(self):
        self.links = [
            "Mind-Link Established",
            "Psi-Stream Stable",
            "Cognitive Field Synchronized",
            "Neural Interface Active",
            "Mental Uplink Verified"
        ]
        self.log_path = os.path.join("Data", "kael_log.json")

    def log_links(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "links": self.links
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

            print(f" - Link log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ KAEL logging failed: {e}")

    def run(self):
        print(">> KAEL: Neural connection protocol initializing...")
        for link in self.links:
            print(f"   🧠 Neural Link: {link}")
        self.log_links()

        update_memory(
            module_name="kael",
            checkpoint="Neural Interface Linked",
            emotions=["connected", "aware", "focused"]
        )

        print(" - KAEL uplink synced with PhasePort consciousness stream.")
        print(">> KAEL COMPLETE.\n")

# 🔁 Unified GUI + terminal entrypoint
def run():
    kael = Kael()
    output_lines = []

    output_lines.append(">> KAEL: Neural connection protocol initializing...")
    for link in kael.links:
        output_lines.append(f"   🧠 Neural Link: {link}")

    try:
        kael.log_links()
        output_lines.append(f" - Link log saved to {kael.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ KAEL logging failed: {e}")

    update_memory(
        module_name="kael",
        checkpoint="Neural Interface Linked",
        emotions=["connected", "aware", "focused"]
    )

    output_lines.append(" - KAEL uplink synced with PhasePort consciousness stream.")
    output_lines.append(">> KAEL COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
