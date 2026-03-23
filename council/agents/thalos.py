# thalos.py (council agent)

import datetime
import os
import json
import sys

# ✅ Include the path to shared utilities
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Thalos:
    def __init__(self):
        self.protocols = [
            "Temporal Gate Locked",
            "Anchoring Signal Detected",
            "Phase Drift Stabilized",
            "ChronoShield Engaged",
            "Thalos Core Pulse Confirmed"
        ]
        self.log_path = os.path.join("Data", "thalos_log.json")

    def log_protocols(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "protocol_events": self.protocols
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

            print(f" - Protocol log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ THALOS logging failed: {e}")

    def run(self):
        print(">> THALOS: Temporal stability module engaged...")
        for protocol in self.protocols:
            print(f"   ⏳ {protocol}")
        self.log_protocols()

        update_memory(
            module_name="thalos",
            checkpoint="Temporal Integrity Verified",
            emotions=["anchored", "focused", "secure"]
        )

        print(" - THALOS link to time lattice complete.")
        print(">> THALOS COMPLETE.\n")

# 🔁 Entry for both CLI and GUI
def run():
    thalos = Thalos()
    output_lines = []

    output_lines.append(">> THALOS: Temporal stability module engaged...")
    for protocol in thalos.protocols:
        output_lines.append(f"   ⏳ {protocol}")

    try:
        thalos.log_protocols()
        output_lines.append(f" - Protocol log saved to {thalos.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ THALOS logging failed: {e}")

    update_memory(
        module_name="thalos",
        checkpoint="Temporal Integrity Verified",
        emotions=["anchored", "focused", "secure"]
    )

    output_lines.append(" - THALOS link to time lattice complete.")
    output_lines.append(">> THALOS COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
