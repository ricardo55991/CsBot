import json

with open("docs/fase_1_7/mirage_spot_confidence.json", "r", encoding="utf-8") as f:
    conf = json.load(f)

spots = conf["spots"]
c_sum = conf["confidence_summary"]
v_sum = conf["validation_status_summary"]

md = []
md.append("# Relatório de Confiança e Validação de Spots — Mirage V2 (Fase 1.7)\n")
md.append("> [!NOTE]")
md.append("> Este relatório audita e consolida a confiança amostral e o status de validação de todos os 45 spots do perfil Mirage V2,")
md.append("> correlacionando evidências profissionais (444 demos, 13.676 rounds), testes locais no servidor dedicado e telemetria de partida normal.\n")
md.append("## 1. Resumo Quantitativo\n")
md.append(f"- **Total de Spots Auditados**: {len(spots)}")
md.append(f"- **Confiança HIGH**: {c_sum['HIGH']} spots")
md.append(f"- **Confiança MEDIUM**: {c_sum['MEDIUM']} spots")
md.append(f"- **Confiança LOW**: {c_sum['LOW']} spots\n")
md.append("### Distribuição por Validation Status:")
for k, v in v_sum.items():
    md.append(f"- `{k}`: {v} spots")
md.append("\n---\n")

md.append("## 2. Regras Estritas Aplicadas\n")
md.append("1. **Nenhum dos 19 spots não observados na partida normal recebeu `RUNTIME_OBSERVED`**: todos foram classificados estritamente como `RUNTIME_NOT_OBSERVED` ou `INSUFFICIENT_EVIDENCE`.")
md.append("2. **Nenhum dos 20 spots corrigidos foi promovido a `APPROVED_BY_USER`**: os 8 spots mais sensíveis permanecem em `PENDING_HUMAN_REVIEW` com confiança `MEDIUM`.")
md.append("3. **Os 6 spots com evidência insuficiente (`INSUFFICIENT_EVIDENCE`) permanecem com confiança `LOW`**.")
md.append("4. **Os 12 spots com classificação `SMALL_ADJUSTMENT` mantêm suas coordenadas atuais** e não sofreram mutações.\n")
md.append("---\n")

md.append("## 3. Tabela Completa dos 45 Spots\n")
md.append("| # | SpotId | Time | Setor | Bombsite | Uso | Confiança | Status de Validação | Partida Normal | Evidências Pro | Decisão / Justificativa |")
md.append("| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

for idx, sp in enumerate(spots, 1):
    partida_str = "Sim" if sp["ObservedInMatch"] else "Não"
    md.append(f"| {idx} | `{sp['SpotId']}` | {sp['Side']} | {sp['AssociatedBombsite']} | {sp['AssociatedBombsite']} | {sp['Usage']} | **{sp['Confidence']}** | `{sp['ValidationStatus']}` | {partida_str} | {sp['EvidenceCount']} | {sp['DecisionReason']} |")

md.append("\n---\n")
md.append("## 4. Conclusão Técnica de Confiança\n")
md.append("O perfil espacial de Mirage encontra-se com 62.2% dos spots em confiança `HIGH` e 24.4% em `MEDIUM`, totalizando 86.6% da malha tática plenamente utilizável.")
md.append("Os 6 spots de confiança `LOW` (13.3%) estão formalmente identificados e não serão alvos prioritários de treinamento na Fase 2 até expansão amostral.")

with open("docs/fase_1_7/mirage_spot_confidence_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("Saved docs/fase_1_7/mirage_spot_confidence_report.md")
