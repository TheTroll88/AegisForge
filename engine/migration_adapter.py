import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import importlib
import os
import sys

# Ensure relative paths work
sys.path.append(os.path.abspath("council/Functions"))

COUNCIL = [
    "astra", "calliope", "ciel", "deimos", "echo",
    "eos", "kael", "lyra", "mira", "nyx",
    "orion", "seraph", "thalos", "vira"
]

def run_module(name, log_area):
    try:
        module = importlib.import_module(name)
        if hasattr(module, "run"):
            output = module.run()
            log_area.insert(tk.END, f"\n>> {name.upper()} OUTPUT:\n{output}\n")
        else:
            log_area.insert(tk.END, f"\n[✘] {name}.py has no run() method.\n")
    except Exception as e:
        log_area.insert(tk.END, f"\n[!] Error loading {name}.py: {str(e)}\n")

def run_all(log_area):
    for name in COUNCIL:
        run_module(name, log_area)

def launch_gui():
    root = tk.Tk()
    root.title("AegisForge Adapter Interface")

    tk.Label(root, text="AegisForge Control Panel", font=("Segoe UI", 14, "bold")).pack(pady=10)

    button_frame = tk.Frame(root)
    button_frame.pack()

    log_area = scrolledtext.ScrolledText(root, width=80, height=25, bg="#111", fg="#00FFAA", font=("Consolas", 10))
    log_area.pack(padx=10, pady=10)

    for name in COUNCIL:
        tk.Button(button_frame, text=name.capitalize(), width=10,
                  command=lambda n=name: run_module(n, log_area)).pack(side=tk.LEFT, padx=2, pady=2)

    tk.Button(root, text="Run All", command=lambda: run_all(log_area), bg="darkgreen", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    print("\n=== AegisForge Adapter (Interface Mode) ===")
    print("[🧠] Memory core linked → Nathaniel (Founder)\n")
    launch_gui()
