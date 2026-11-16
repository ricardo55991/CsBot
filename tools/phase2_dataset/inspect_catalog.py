import json
import hashlib
from pathlib import Path

def inspect():
    dm_path = Path("src/CsBotManager/MapProfiles/de_mirage.json")
    v3_path = Path("docs/spot_recording/mirage_spots_enriched_live_v3.json")
    pdf_path = Path("docs/fase_1_7/catalogo_mirage_50_spots_source2_final.pdf")

    print(f"Checking {dm_path}: exists={dm_path.exists()}")
    print(f"Checking {v3_path}: exists={v3_path.exists()}")
    print(f"Checking {pdf_path}: exists={pdf_path.exists()}")

    dm = json.loads(dm_path.read_text(encoding="utf-8"))
    spots = dm.get("spots", [])
    print(f"de_mirage.json spots count: {len(spots)}")

    v3 = json.loads(v3_path.read_text(encoding="utf-8"))
    print(f"mirage_spots_enriched_live_v3.json spots count: {len(v3)}")

    # Check sha256 of sources
    dm_sha256 = hashlib.sha256(dm_path.read_bytes()).hexdigest()
    pdf_sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    print(f"de_mirage.json SHA256: {dm_sha256}")
    print(f"PDF SHA256: {pdf_sha256}")

    for i, s in enumerate(spots, 1):
        print(f"{i:02d}: {s['id']} | {s.get('name')} | Sector: {s.get('sector')} | Side: {s.get('side')}")

if __name__ == "__main__":
    inspect()
