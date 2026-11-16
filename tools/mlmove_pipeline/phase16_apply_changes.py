"""
Executa a correcao controlada de de_mirage.json conforme a Fase 1.6:
1. Backup de de_mirage.json para src/CsBotManager/MapProfiles/backups/de_mirage.v1_backup.json
2. Calculo SHA-256 V1
3. Aplicacao estrita de apenas spots com ManualDecision == "APPROVED"
4. Preservacao dos SpotIds e de todos os spots SMALL_ADJUSTMENT / INSUFFICIENT_EVIDENCE / VALID
5. map_profile_version incrementado para 2
6. Calculo SHA-256 V2
7. Geracao de changelog detalhado em JSON e Markdown
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
PROFILE_PATH = ROOT / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"
BACKUP_DIR = ROOT / "src" / "CsBotManager" / "MapProfiles" / "backups"
BACKUP_PATH = BACKUP_DIR / "de_mirage.v1_backup.json"
REVIEW_PATH = ROOT / "docs" / "fase_1_6" / "mirage_spot_manual_review.json"
CHANGELOG_JSON = ROOT / "docs" / "fase_1_6" / "de_mirage_v1_to_v2_changelog.json"
CHANGELOG_MD = ROOT / "docs" / "fase_1_6" / "de_mirage_v1_to_v2_changelog.md"


def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # 1 & 2. Backup e SHA256 V1 (sempre calcula SHA-256 V1 e OldPosition a partir do backup original V1)
    if not BACKUP_PATH.exists():
        shutil.copy2(PROFILE_PATH, BACKUP_PATH)
        print(f"[+] Backup criado: {BACKUP_PATH}")
    else:
        print(f"[*] Backup ja existente: {BACKUP_PATH}")

    sha256_v1 = get_sha256(BACKUP_PATH)
    print(f"[+] SHA-256 V1: {sha256_v1}")

    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        backup_profile = json.load(f)
    v1_spots_map = {s["id"]: s for s in backup_profile.get("spots", [])}

    # 3. Ler revisao manual
    reviews = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    approved_map = {r["SpotId"]: r for r in reviews if r.get("ManualDecision") == "APPROVED"}
    print(f"[+] Spots aprovados para atualizacao: {len(approved_map)}")

    # 4. Ler perfil atual
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # 5. Atualizar map_profile_version
    profile["map_profile_version"] = 2

    # 6. Atualizar spots aprovados
    changelog = []
    spots = profile.get("spots", [])
    updated_count = 0

    for s in spots:
        sid = s.get("id")
        if sid in approved_map:
            rev = approved_map[sid]
            v1_s = v1_spots_map.get(sid, s)
            old_pos = [float(v1_s["x"]), float(v1_s["y"]), float(v1_s["z"])]
            new_pos = rev["ProposedPosition"]

            s["x"] = round(float(new_pos[0]), 1)
            s["y"] = round(float(new_pos[1]), 1)
            s["z"] = round(float(new_pos[2]), 1)

            entry = {
                "SpotId": sid,
                "Name": s.get("name"),
                "OldPosition": old_pos,
                "NewPosition": [s["x"], s["y"], s["z"]],
                "VisualLandmark": rev["VisualLandmark"],
                "CurrentValvePlace": rev["CurrentValvePlace"],
                "ProposedValvePlace": rev["ProposedValvePlace"],
                "DecisionReason": rev["DecisionReason"]
            }
            changelog.append(entry)
            updated_count += 1

    print(f"[+] Total de spots atualizados no JSON: {updated_count}")

    # Salva de_mirage.json atualizado
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Copia tambem para bin/Debug e bin/Release para deploy imediato
    for target in [
        ROOT / "src" / "CsBotManager" / "bin" / "Debug" / "net10.0" / "MapProfiles" / "de_mirage.json",
        ROOT / "src" / "CsBotManager" / "bin" / "Release" / "net10.0" / "MapProfiles" / "de_mirage.json",
        Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\MapProfiles\de_mirage.json")
    ]:
        if target.parent.exists():
            shutil.copy2(PROFILE_PATH, target)
            print(f"[+] Deploy de de_mirage.json para: {target}")

    sha256_v2 = get_sha256(PROFILE_PATH)
    print(f"[+] SHA-256 V2: {sha256_v2}")

    # Salva changelog JSON
    changelog_payload = {
        "map": "de_mirage",
        "old_version": 1,
        "new_version": 2,
        "sha256_v1": sha256_v1,
        "sha256_v2": sha256_v2,
        "total_spots": len(spots),
        "updated_spots_count": len(changelog),
        "kept_spots_count": len(spots) - len(changelog),
        "updates": changelog
    }
    CHANGELOG_JSON.write_text(json.dumps(changelog_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Changelog JSON gerado: {CHANGELOG_JSON}")

    # Salva changelog Markdown
    md_lines = [
        "# Changelog de Atualização — Perfil Mirage V1 -> V2 (Fase 1.6)",
        "",
        f"- **Arquivo**: `src/CsBotManager/MapProfiles/de_mirage.json`",
        f"- **Versão Anterior**: `1` | **SHA-256 V1**: `{sha256_v1}`",
        f"- **Versão Nova**: `2` | **SHA-256 V2**: `{sha256_v2}`",
        f"- **Backup**: `src/CsBotManager/MapProfiles/backups/de_mirage.v1_backup.json`",
        f"- **Spots Atualizados**: **{len(changelog)}** (apenas `APPROVED`)",
        f"- **Spots Mantidos Inalterados**: **{len(spots) - len(changelog)}** (7 `VALID` + 12 `SMALL_ADJUSTMENT` + 6 `INSUFFICIENT_EVIDENCE`)",
        "",
        "## Tabela de Modificações dos Spots Aprovados",
        "",
        "| SpotId | Nome | OldPosition | NewPosition | Valve Place (Old -> New) | Landmark Visual |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for c in changelog:
        old_p = f"`[{c['OldPosition'][0]:.1f}, {c['OldPosition'][1]:.1f}, {c['OldPosition'][2]:.1f}]`"
        new_p = f"`[{c['NewPosition'][0]:.1f}, {c['NewPosition'][1]:.1f}, {c['NewPosition'][2]:.1f}]`"
        pl = f"`{c['CurrentValvePlace']}` -> `{c['ProposedValvePlace']}`"
        md_lines.append(f"| `{c['SpotId']}` | {c['Name']} | {old_p} | {new_p} | {pl} | {c['VisualLandmark']} |")

    CHANGELOG_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[+] Changelog Markdown gerado: {CHANGELOG_MD}")


if __name__ == "__main__":
    main()
