"""
Validação em lote de todos os componentes da esteira intermediate_demo_acquisition
em modo --dry-run e --self-test.
Gera relatório JSON determinístico e saída cirúrgica.
"""
import subprocess
import sys
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

COMMANDS = [
    ("validate_skill_bucket", [sys.executable, "tools/intermediate_demo_acquisition/validate_skill_bucket.py", "--self-test"]),
    ("verify_archive", [sys.executable, "tools/intermediate_demo_acquisition/verify_archive.py", "--self-test"]),
    ("extract_demo", [sys.executable, "tools/intermediate_demo_acquisition/extract_demo.py", "--self-test"]),
    ("deduplicate_demo", [sys.executable, "tools/intermediate_demo_acquisition/deduplicate_demo.py", "--self-test"]),
    ("resume_download", [sys.executable, "tools/intermediate_demo_acquisition/resume_download.py", "--self-test"]),
    ("ingest_opt_in_demo", [sys.executable, "tools/intermediate_demo_acquisition/ingest_opt_in_demo.py", "--self-test"]),
    ("discover_matches", [sys.executable, "tools/intermediate_demo_acquisition/discover_matches.py", "--dry-run"]),
    ("fetch_match_metadata", [sys.executable, "tools/intermediate_demo_acquisition/fetch_match_metadata.py", "--dry-run"]),
    ("build_manifest", [sys.executable, "tools/intermediate_demo_acquisition/build_manifest.py", "--dry-run"]),
]

def main():
    results = []
    for name, cmd in COMMANDS:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        results.append({
            "name": name,
            "cmd": " ".join(cmd[1:]),
            "exit_code": proc.returncode,
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "stdout_preview": proc.stdout.strip()[:200] if proc.stdout else "",
            "stderr_preview": proc.stderr.strip()[:200] if proc.stderr else ""
        })

    all_passed = all(r["status"] == "PASS" for r in results)
    summary = {
        "schema": "csbot.acquisition_tools_dry_run_validation.v1",
        "all_passed": all_passed,
        "total_commands": len(results),
        "passed_count": sum(1 for r in results if r["status"] == "PASS"),
        "failed_count": sum(1 for r in results if r["status"] == "FAIL"),
        "results": results
    }

    out_path = REPO_ROOT / "training_runs" / "intermediate_domain_study" / "dry_run_validation_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"DRY_RUN_VALIDATION: {'ALL_PASS' if all_passed else 'SOME_FAIL'} ({summary['passed_count']}/{summary['total_commands']}) -> {out_path.name}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
