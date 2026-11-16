import json

transcript_path = r"C:\Users\ricar\.gemini\antigravity\brain\d65e2bde-5cae-4311-b714-4707e256a192\.system_generated\logs\transcript.jsonl"
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT":
            content = obj.get("content", "")
            if "FASE 1.7:" in content:
                # print chunks
                print("LEN:", len(content))
                for i in range(0, len(content), 3000):
                    print(f"--- CHUNK {i} ---")
                    print(content[i:i+3000])
                break
