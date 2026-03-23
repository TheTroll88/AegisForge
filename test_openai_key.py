import requests
import subprocess

# Get the actual key from vault
result = subprocess.run(
    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', '.\\secure_vault.ps1', '-Action', 'get', '-Name', 'AI_API_KEY'],
    capture_output=True, text=True, cwd='.'
)
key = result.stdout.strip()

print(f"Key: {key[:30]}...{key[-10:]}")
print(f"Length: {len(key)}")
print(f"Repr: {repr(key)}")

# Test direct API call
try:
    resp = requests.get(
        'https://api.openai.com/v1/models',
        headers={'Authorization': f'Bearer {key}'},
        timeout=10
    )
    print(f"OpenAI API response: {resp.status_code}")
    if resp.status_code != 200:
        err = resp.json()
        print(f"Error: {err}")
    else:
        print("✅ Key is VALID")
except Exception as e:
    print(f"Exception: {e}")
