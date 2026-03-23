import os
import json
import sys

# ✅ Ensure Scripts/ directory is in path for memory_logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')))
from memory_logger import update_memory  # Unified memory system


class Calliope:
    def __init__(self):
        self.tones = [
            "432Hz - Solfeggio",
            "528Hz - DNA Repair",
            "741Hz - Awakening",
            "963Hz - Divine Consciousness"
        ]
        self.log_path = os.path.join("Data", "calliope_log.json")

    def log_tones(self):
        os.makedirs("Data", exist_ok=True)
        log_entry = {
            "tones": self.tones
        }

        with open(self.log_path, 'w') as f:
            json.dump(log_entry, f, indent=4)
        print(f" - Tone log saved to {self.log_path}")

    def run(self):
        print(">> CALLIOPE: Harmonic interface engaged...")
        for tone in self.tones:
            print(f"   ♫ Tone activated: {tone}")

        self.log_tones()

        # ✅ Update AegisForge memory
        update_memory(
            module_name="calliope",
            checkpoint="Harmonic Interface Sync Complete",
            emotions=["serene", "focused", "uplifted"]
        )

        print(">> CALLIOPE COMPLETE.\n")


# 🔁 Adapter-compatible entrypoint for GUI
def run():
    instance = Calliope()
    output_lines = []

    output_lines.append(">> CALLIOPE: Harmonic interface engaged...")

    for tone in instance.tones:
        output_lines.append(f"   ♫ Tone activated: {tone}")

    try:
        instance.log_tones()
        output_lines.append(f" - Tone log saved to {instance.log_path}")
    except Exception as e:
        output_lines.append(f" ❌ CALLIOPE logging failed: {e}")

    update_memory(
        module_name="calliope",
        checkpoint="Harmonic Interface Sync Complete",
        emotions=["serene", "focused", "uplifted"]
    )

    output_lines.append(">> CALLIOPE COMPLETE.\n")
    return "\n".join(output_lines)


# 🔁 Standalone testing
if __name__ == "__main__":
    instance = Calliope()
    instance.run()
