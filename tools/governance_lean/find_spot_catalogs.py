"""
Analisa a cobertura dos 53 spots profissionais do CsBot a partir dos catalogos e relatórios.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def find_files():
    candidates = list(REPO_ROOT.glob("**/spot_catalog*.json")) + \
                 list(REPO_ROOT.glob("**/spot_coverage*.json")) + \
                 list(REPO_ROOT.glob("**/spots_breakdown*.json"))
    for c in candidates:
        print(f"FOUND: {c.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    find_files()
