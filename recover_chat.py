import sqlite3
import json
import os
import datetime

db = r'C:\Users\natha\AppData\Roaming\Code\User\workspaceStorage\1774230028427\state.vscdb'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Extract all conversation turns from interactive-session
cur.execute("SELECT value FROM ItemTable WHERE key = 'memento/interactive-session'")
row = cur.fetchone()
data = json.loads(row[0])

history = data.get('history', {})
output = []

for session_name, turns in history.items():
    output.append(f"# Recovered Session: {session_name}")
    output.append(f"# Turns: {len(turns)}")
    output.append("")
    
    for i, turn in enumerate(turns):
        input_text = turn.get('inputText', '')
        mode = turn.get('mode', {}).get('id', '?')
        model = turn.get('selectedModel', {}).get('identifier', '?')
        attachments = turn.get('attachments', [])
        
        output.append(f"## Turn {i+1}")
        output.append(f"Mode: {mode} | Model: {model}")
        if attachments:
            for att in attachments:
                att_name = att.get('name', 'unknown')
                att_kind = att.get('kind', '?')
                refs = att.get('references', [])
                ref_paths = []
                for ref in refs:
                    r = ref.get('reference', {})
                    ref_paths.append(r.get('fsPath', r.get('path', '?')))
                output.append(f"Attachment: [{att_kind}] {att_name} -> {', '.join(ref_paths)}")
        output.append("")
        output.append("### User Message:")
        output.append(input_text)
        output.append("")
        output.append("---")
        output.append("")

# Save as markdown
with open('RECOVERED_CONVERSATION.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Saved {len(turns)} conversation turns to RECOVERED_CONVERSATION.md")

# Now also check the other big session for the signature hash thread (session 6)
target_resource2 = 'MGZmMTg5MTQtNzA3My00ODM5LThiOWItNjdlNGY5ZWI1YzY4'
for session_name, turns in history.items():
    print(f"\nSession '{session_name}': {len(turns)} turns")
    for i, t in enumerate(turns):
        preview = t.get('inputText', '')[:120].replace('\n', ' ')
        print(f"  {i}: {preview}")

conn.close()
