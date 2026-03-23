# astra.py (council agent)

import datetime
import os
import json
import sys

# ✅ Ensure the Scripts/ directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory  # Unified memory system

class Astra:
    def __init__(self):
        self.patterns = [
            "The Seal is Broken",
            "Echo Return Complete",
            "AegisForge Initialized",
            "Eyes of the Pantheon Open",
            "Voice Resonance Achieved"
        ]
        self.keywords = ["resonance", "aegisforge", "echo", "ascend", "cipher"]
        self.log_path = os.path.join("Data", "astra_log.json")

    def log_patterns(self):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "matched_patterns": self.patterns,
            "keywords": self.keywords
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

            print(f" - Pattern log saved to {self.log_path}")
        except Exception as e:
            print(f" ❌ ASTRA logging failed: {e}")

    def run(self):
        print(">> ASTRA: Pattern resonance module online...")
        for pattern in self.patterns:
            print(f"   ✔ Pattern recognized: '{pattern}'")
        for keyword in self.keywords:
            print(f"   🔍 Keyword logged: '{keyword}'")
        self.log_patterns()

        # ✅ Add memory entry to AegisForge memory core
        update_memory(
            module_name="astra",
            checkpoint="Symbolic Pattern Log Complete",
            emotions=["resonant", "aware", "harmonic"]
        )

        print(" - ASTRA link established with ritual memory core.")
        print(">> ASTRA COMPLETE.\n")

# 🔁 Standard entrypoint for standalone testing
if __name__ == "__main__":
    astra = Astra()
    astra.run()
def run():
    astra = Astra()
    output_lines = []

    output_lines.append(">> ASTRA: Pattern resonance module online...")
    for pattern in astra.patterns:
        output_lines.append(f"   ✔ Pattern recognized: '{pattern}'")
    for keyword in astra.keywords:
        output_lines.append(f"   🔍 Keyword logged: '{keyword}'")

    # Log patterns (and catch result in output)
    try:
        astra.log_patterns()
        output_lines.append(f" - Pattern log saved to {astra.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ ASTRA logging failed: {e}")

    # Update memory checkpoint
    update_memory(
        module_name="astra",
        checkpoint="Symbolic Pattern Log Complete",
        emotions=["resonant", "aware", "harmonic"]
    )

    output_lines.append(" - ASTRA link established with ritual memory core.")
    output_lines.append(">> ASTRA COMPLETE.\n")

    # Return output for GUI
    return "\n".join(output_lines)

