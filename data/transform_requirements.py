import json
import re
import os

input_file = r"d:\Antigravity\AI_Agent_PM_PRJ\data\clean_requirements.json"
output_file = r"d:\Antigravity\AI_Agent_PM_PRJ\data\clean_requirements.json"

# Read original data if available, or we might need to re-parse.
# Wait, we already overwrote clean_requirements.json. So we read it, process the `requirement` field.
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    req_text = item.get("requirement", "")
    # Normalize whitespaces: replace \r\n, \n, \t and multiple spaces with a single space
    req_text = re.sub(r'\s+', ' ', req_text).strip()
    item["requirement"] = req_text

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Re-formatted {len(data)} items to clean up newlines.")
