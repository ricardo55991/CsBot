"""Verificacao mecanica (somente leitura) dos artefatos M4/M7 da FASE 2A-INTERMEDIATE.

Uso:
    python .agents/teamwork/implementer_data_2a_int_1/verify_artifacts.py

Nao escreve nada no repositorio. Imprime, para cada artefato:
  caminho relativo | bytes | SHA-256 (64 hex) | record_count | (N/D)
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
IC = BASE / "datasets" / "mirage_domains" / "intermediate_competitive"

ARTIFACTS = [
    IC / "intermediate_demo_inventory_v1.json",
    IC / "intermediate_npz_manifest_v1.json",
    IC / "pilot_download_manifest.json",
    IC / "quarantine_manifest.json",
    BASE / "training_runs" / "intermediate_domain_study" / "intermediate_splits_proposal.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def walk(node, path="$"):
    """Gera (json_path, chave, valor) para todo par chave/valor de dicionario."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}"
            yield here, key, value
            yield from walk(value, here)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}[{index}]")


def aggregations(payload):
    """Coleta blocos que declararam agregacao explicita (numerator/denominator)."""
    found = []
    for _, key, value in walk(payload):
        if isinstance(value, dict) and "numerator" in value and "denominator" in value:
            found.append((value.get("numerator"), value.get("denominator"), value.get("status") or value.get("aggregation_status")))
    return found


def main() -> int:
    print("=" * 100)
    print("VERIFICACAO MECANICA DOS ARTEFATOS M4/M7 — FASE 2A-INTERMEDIATE")
    print("=" * 100)

    failures = []
    for artifact in ARTIFACTS:
        if not artifact.is_file():
            failures.append(f"AUSENTE: {artifact}")
            continue
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        size = artifact.stat().st_size
        digest = sha256(artifact)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            failures.append(f"SHA-256 invalido em {artifact}")
        rel = artifact.relative_to(BASE).as_posix()
        record_count = payload.get("record_count")
        npz_count = payload.get("npz_count")
        print(f"\n{rel}")
        print(f"  bytes={size}  sha256={digest}")
        print(f"  record_count={record_count!r}  npz_count={npz_count!r}")
        aggs = aggregations(payload)
        if aggs:
            for numerator, denominator, status in aggs[:6]:
                print(f"  agregacao explicita: ({numerator}/{denominator}) status={status!r}")
            if len(aggs) > 6:
                print(f"  ... +{len(aggs) - 6} blocos de agregacao")
        else:
            print("  agregacao explicita: NENHUM BLOCO numerator/denominator")
        if size <= 0:
            failures.append(f"TAMANHO ZERO: {artifact}")

    print("\n" + "=" * 100)
    if failures:
        print("FALHAS:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("TODOS OS 5 ARTEFATOS PRESENTES, NAO VAZIOS, JSON VALIDO E COM SHA-256 DE 64 HEX.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
