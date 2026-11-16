import os
from pathlib import Path

dem_dir = Path(r"F:\CS2_MLMove_Pipeline\raw_demos")
dems = list(dem_dir.rglob("*.dem"))
print(f"Found {len(dems)} DEM files:")
for d in sorted(dems):
    sz_mb = d.stat().st_size / (1024 * 1024)
    print(f"  {d.name} ({sz_mb:.1f} MB) -> {d}")
