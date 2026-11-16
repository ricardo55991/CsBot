"""Harness de auditoria do mutation_probe com prova de não-contaminação (somente leitura no repo).

- Fixa o diretório temporário em %TEMP%\\csbot_2a_int_mutation_probe (concreto, não anônimo).
- Registra cada TemporaryDirectory criado (caminho absoluto).
- Conta arquivos em datasets/ e tools/ ANTES e DEPOIS da execução.
- Não modifica nada do repositório.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(".").resolve()
PROBE = ROOT / ".agents/teamwork/implementer_data_2a_int_1/mutation_probe.py"

TEMP_BASE = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "csbot_2a_int_mutation_probe"
TEMP_BASE.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEMP_BASE)

created_dirs: list[str] = []

_original_temporary_directory = tempfile.TemporaryDirectory


class LoggingTemporaryDirectory(_original_temporary_directory):  # type: ignore[misc]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        created_dirs.append(self.name)


tempfile.TemporaryDirectory = LoggingTemporaryDirectory  # type: ignore[assignment]


def count_files(base: Path) -> tuple[int, int, list[str]]:
    """(total de arquivos, total de .pyc, lista de caminhos relativos)."""
    total = 0
    pyc = 0
    rels: list[str] = []
    for path in base.rglob("*"):
        if path.is_file():
            total += 1
            if path.suffix == ".pyc":
                pyc += 1
            rels.append(path.relative_to(ROOT).as_posix())
    return total, pyc, sorted(rels)


def snapshot() -> dict[str, tuple[int, int, set[str]]]:
    out = {}
    for name in ("datasets", "tools", "training_runs", "tests", "src"):
        base = ROOT / name
        total, pyc, rels = count_files(base) if base.is_dir() else (0, 0, [])
        out[name] = (total, pyc, set(rels))
    return out


print(f"TEMP base concreta: {TEMP_BASE}")
print(f"tempfile.tempdir = {tempfile.tempdir}")
print(f"PYTHONPYCACHEPREFIX = {os.environ.get('PYTHONPYCACHEPREFIX')!r}")

before = snapshot()
print("\n=== ANTES ===")
for name, (total, pyc, _) in before.items():
    print(f"  {name:<14} arquivos={total:<6} .pyc={pyc}")

spec = importlib.util.spec_from_file_location("mutation_probe_audited", PROBE)
module = importlib.util.module_from_spec(spec)
sys.modules["mutation_probe_audited"] = module
spec.loader.exec_module(module)  # type: ignore[union-attr]

print("\n=== EXECUÇÃO DO PROBE ===")
exit_code = module.main()

print("\n=== DIRETÓRIOS TEMPORÁRIOS CRIADOS PELO PROBE ===")
for i, directory in enumerate(created_dirs, 1):
    print(f"  {i:02d}. {directory}  (existe_apos_limpeza={Path(directory).exists()})")
print(f"  total de cópias temporárias = {len(created_dirs)}")

after = snapshot()
print("\n=== DEPOIS ===")
for name, (total, pyc, _) in after.items():
    print(f"  {name:<14} arquivos={total:<6} .pyc={pyc}")

print("\n=== DIFERENÇAS ===")
violations = 0
for name in before:
    b_total, b_pyc, b_set = before[name]
    a_total, a_pyc, a_set = after[name]
    added = sorted(a_set - b_set)
    removed = sorted(b_set - a_set)
    delta = a_total - b_total
    print(f"  {name:<14} delta_arquivos={delta:+d}  .pyc {b_pyc}->{a_pyc}  adicionados={added}  removidos={removed}")
    non_pyc_added = [p for p in added if not p.endswith(".pyc")]
    if non_pyc_added or removed:
        violations += 1

print(f"\nVIOLACOES_DE_ISOLAMENTO = {violations}")
print(f"PROBE_EXIT_CODE = {exit_code}")
