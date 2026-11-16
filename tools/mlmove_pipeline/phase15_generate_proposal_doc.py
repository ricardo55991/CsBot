"""
Gera docs/fase_1_5/mirage_spot_change_proposal.md a partir de docs/fase_1_5/mirage_spot_audit.json
e docs/fase_1_5/mirage_spot_clusters.json, sem alterar src/CsBotManager/MapProfiles/de_mirage.json.
"""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
OUT_DIR = ROOT / "docs" / "fase_1_5"


def fmt_pos(p):
    if p is None:
        return "— (manter atual)"
    return f"`[{p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f}]`"


def main():
    audit_data = json.loads((OUT_DIR / "mirage_spot_audit.json").read_text(encoding="utf-8"))
    clusters_data = json.loads((OUT_DIR / "mirage_spot_clusters.json").read_text(encoding="utf-8"))

    audits = audit_data["audit"]
    counts = audit_data["classification_counts"]

    lines = []
    lines.append("# Proposta Controlada de Revisão Espacial — `de_mirage.json` (Fase 1.5)")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> **Nenhuma alteração foi aplicada ao arquivo `src/CsBotManager/MapProfiles/de_mirage.json`.**")
    lines.append("> Este documento apresenta a auditoria individual dos **45 TacticalSpots** atuais da Mirage contra os **176 clusters 3D de permanência real** (`69.320` episódios de hold estático com `v2d < 35 u/s`, duração $\\ge 1,5\\text{s}$ e deriva $\\le 64\\text{u}$) extraídos das **444 demos profissionais** e validados contra os `last_place_name` oficiais da Valve.")
    lines.append("")
    lines.append("## 1. Resumo Executivo da Auditoria dos 45 Spots")
    lines.append("")
    lines.append("| Classificação | Quantidade | Significado e Ação Recomendada |")
    lines.append("| :--- | :---: | :--- |")
    for cls_name, desc in [
        ("WRONG_SECTOR", "Coordenada atual cai em outro `last_place_name` da Valve (erro crasso de setor). **Substituir pelo Medoid do cluster compatível.**"),
        ("WRONG_HEIGHT", "Coordenada XY caminhável, mas cota `Z` incompatível com os pisos observados ou setor errado. **Substituir pelo Medoid 3D correto.**"),
        ("SMALL_ADJUSTMENT", "Setor correto, mas deslocado entre `65u` e `260u` do pico real de hold profissional. **Ajuste fino opcional para o Medoid.**"),
        ("INSUFFICIENT_EVIDENCE", "Setor correto, porém poucos holds estáticos $\\ge 1,5\\text{s}$ em raio de `96u` (comum em spots de passagem/entry/plant). **Revisar candidato mais próximo ou manter.**"),
        ("VALID", "Setor, altura, caminhabilidade empírica e evidência profissional confirmados ($\\le 64\\text{u}$ de cluster ou $\\ge 40$ demos locais). **Manter inalterado.**"),
        ("AMBIGUOUS", "Fronteira entre dois places da Valve com pureza kNN $< 0,55$. **Inspecionar via `setpos`.**"),
        ("UNREACHABLE", "Nenhum pé de jogador vivo observado em raio de `32u` em qualquer altura. **Substituir obrigatoriamente.**"),
    ]:
        c = counts.get(cls_name, 0)
        lines.append(f"| `{cls_name}` | **{c}** | {desc} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Tabela Completa de Auditoria e Coordenadas Propostas (45 Spots)")
    lines.append("")
    lines.append("| # | SpotId | Side | Usage | Bomb | CurrentPosition | Place Real (kNN) | Place Esperado | Classificação | ProposedPosition (Medoid) | $\\Delta$ (u) | Evidência (Holds / Demos / Players) | Dwell Mediano | Conf. |")
    lines.append("| :-: | :--- | :-: | :--- | :-: | :--- | :--- | :--- | :--- | :--- | :-: | :---: | :-: | :-: |")

    for idx, a in enumerate(audits, 1):
        sid = a["SpotId"]
        side = a["TeamSide"]
        usage = a["Usage"]
        bomb = a["AssociatedBombsite"]
        cur = fmt_pos(a["CurrentPosition"])
        real_pl = f"`{a['ActualValvePlace']}` ({a['ActualPlacePurity']:.2f})"
        exp_pl = ", ".join(f"`{x}`" for x in a["ExpectedValvePlace"])
        cls = f"`{a['CurrentClassification']}`"
        prop = fmt_pos(a["ProposedPosition"])
        shift = f"{a['ProposalShift_u']:.0f}u" if a["ProposedPosition"] else "0u"
        ev = f"{a['EvidenceCount']} / {a['DemoDiversity']}d / {a['PlayerDiversity']}p"
        dwell = f"{a['HoldDurationMedian']:.2f}s" if a["HoldDurationMedian"] is not None else "—"
        conf = f"{a['Confidence']:.2f}"
        lines.append(f"| {idx} | `{sid}` | {side} | {usage} | {bomb} | {cur} | {real_pl} | {exp_pl} | {cls} | {prop} | {shift} | {ev} | {dwell} | {conf} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Comandos `setpos` para Inspeção Visual no CS2 (Antes vs. Depois)")
    lines.append("")
    lines.append("Para inspecionar manualmente no servidor local ou cliente CS2 (`sv_cheats 1`), copie e cole os comandos abaixo no console (`~`):")
    lines.append("")
    lines.append("### 3.1. Spots Críticos com `WRONG_SECTOR` ou `WRONG_HEIGHT` (Substituição Obrigatória)")
    lines.append("")
    for a in audits:
        if a["CurrentClassification"] in ("WRONG_SECTOR", "WRONG_HEIGHT", "UNREACHABLE", "AMBIGUOUS"):
            lines.append(f"#### `{a['SpotId']}` — {a['Name']} (`{a['CurrentClassification']}`)")
            lines.append(f"- **Diagnóstico**: {a['ClassificationReason']} | Deslocamento proposto: **{a['ProposalShift_u']:.1f}u** | Resolução: `{a['ProposalResolution']}`")
            lines.append(f"- **Evidência do Medoid Proposto**: `{a['EvidenceCount']}` holds em `{a['DemoDiversity']}` demos (`{a['DemoDiversityPct']}%`), `{a['PlayerDiversity']}` jogadores, dwell mediano `{a['HoldDurationMedian']}s`, confiança `{a['Confidence']:.3f}`.")
            lines.append("```text")
            lines.append(f"// ATUAL (cai em {a['ActualValvePlace']}):")
            lines.append(a["SetposCurrent"])
            if a["SetposProposed"]:
                lines.append(f"// PROPOSTO (Medoid real em {a['ExpectedValvePlace'][0]}):")
                lines.append(a["SetposProposed"])
            lines.append("```")
            lines.append("")

    lines.append("### 3.2. Spots com `SMALL_ADJUSTMENT` ou `INSUFFICIENT_EVIDENCE` (Ajuste Fino / Revisão)")
    lines.append("")
    for a in audits:
        if a["CurrentClassification"] in ("SMALL_ADJUSTMENT", "INSUFFICIENT_EVIDENCE"):
            lines.append(f"#### `{a['SpotId']}` — {a['Name']} (`{a['CurrentClassification']}`)")
            lines.append(f"- **Diagnóstico**: {a['ClassificationReason']} | Resolução: `{a['ProposalResolution']}`")
            lines.append("```text")
            lines.append(f"// ATUAL ({a['ActualValvePlace']}):")
            lines.append(a["SetposCurrent"])
            if a["SetposProposed"]:
                lines.append(f"// CANDIDATO PROPOSTO (shift {a['ProposalShift_u']:.1f}u, {a['DemoDiversity']} demos):")
                lines.append(a["SetposProposed"])
            lines.append("```")
            lines.append("")

    lines.append("### 3.3. Spots `VALID` (Confirmados — Manter Inalterados)")
    lines.append("")
    for a in audits:
        if a["CurrentClassification"] == "VALID":
            lines.append(f"- **`{a['SpotId']}`** ({a['Name']}): `{a['CurrentPosition']}` em `{a['ActualValvePlace']}` — {a['ClassificationReason']} (`{a['SetposCurrent']}`)")

    out_file = OUT_DIR / "mirage_spot_change_proposal.md"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[+] Gerado: {out_file}")


if __name__ == "__main__":
    main()
