import os
import json

def load_member(member_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)  # Go up one level to the root project folder
    member_path = os.path.join(parent_dir, 'Council_of_14_BootPackage', 'Data', f"{member_name.lower()}.json")

    try:
        with open(member_path, 'r') as file:
            profile = json.load(file)
            print(f"\n>>> {member_name.upper()} PROFILE LOADED <<<\n")
            for key, value in profile.items():
                print(f"{key.capitalize()}: {value}")
    except FileNotFoundError:
        print(f"Error: Member profile '{member_name}' not found.")
    except json.JSONDecodeError:
        print("Error: Profile contains invalid JSON.")

def main():
    member = input("Enter council member name to activate (e.g., Calliope): ").strip()
    load_member(member)

if __name__ == "__main__":
    main()