# memory_logger.py

import json
import os
from datetime import datetime

def update_memory(module_name, checkpoint, emotions=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    memory_path = os.path.join(base_dir, 'User_State', 'user_state.json')

    try:
        with open(memory_path, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {
            "user_profile": {},
            "memory_core": {},
            "last_checkpoint": "",
            "emotional_log": [],
            "flags": {}
        }

    # Add emotional log if provided
    if emotions:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module_name,
            "emotions": emotions
        }
        state.setdefault("emotional_log", []).append(log_entry)

    # Update checkpoint and memory core
    state["last_checkpoint"] = checkpoint
    state.setdefault("memory_core", {}).setdefault("linked_modules", [])
    if module_name not in state["memory_core"]["linked_modules"]:
        state["memory_core"]["linked_modules"].append(module_name)

    # Save updated state
    os.makedirs(os.path.dirname(memory_path), exist_ok=True)
    with open(memory_path, 'w') as f:
        json.dump(state, f, indent=4)

    print(f" [💾] Memory updated → {module_name} | Checkpoint: {checkpoint}")
