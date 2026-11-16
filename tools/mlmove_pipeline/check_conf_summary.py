import json

with open("docs/fase_1_7/mirage_spot_confidence.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Confidence summary:", data["confidence_summary"])
print("Validation status summary:", data["validation_status_summary"])
