# echo.py (inside Council_of_14_BootPackage/Functions)

import datetime
import os
import json
import sys

# ✅ Import memory logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory

class Echo:
    def __init__(self):
        self.reflections = [
            "Echo initialized...",
            "Deepwave Response Detected",
            "Resonance Feedback Loop Stable",
            "Interference Pattern Matched",
            "Echo Chamber Alignment Complete"
        ]
        self.log_path = os.path.join("Data", "echo_log.json")

    def log_reflections(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "reflections": self.reflections
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

            print(f" - Echo log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ ECHO logging failed: {e}")

    def run(self):
        print(">> ECHO: Sonic interface link engaged...")
        for line in self.reflections:
            print(f"   🔊 {line}")
        self.log_reflections()

        update_memory(
            module_name="echo",
            checkpoint="Sonic Feedback Loop Complete",
            emotions=["reverberant", "curious", "synchronized"]
        )

        print(" - ECHO chamber synced with auditory node.")
        print(">> ECHO COMPLETE.\n")

# 🔁 GUI + standalone-compatible entrypoint
def run():
    echo = Echo()
    output_lines = []

    output_lines.append(">> ECHO: Sonic interface link engaged...")
    for line in echo.reflections:
        output_lines.append(f"   🔊 {line}")

    try:
        echo.log_reflections()
        output_lines.append(f" - Echo log saved to {echo.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ ECHO logging failed: {e}")

    update_memory(
        module_name="echo",
        checkpoint="Sonic Feedback Loop Complete",
        emotions=["reverberant", "curious", "synchronized"]
    )

    output_lines.append(" - ECHO chamber synced with auditory node.")
    output_lines.append(">> ECHO COMPLETE.\n")

    return "\n".join(output_lines)

if __name__ == "__main__":
    run()
