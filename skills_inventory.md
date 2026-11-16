# Inventário Oficial de Regras e Skills do Workspace CsBot (`skills_inventory.md`)

- **Data de Geração**: `2026-11-07`
- **Escopo**: Workspace Local (`c:\Users\ricar\OneDrive\Documentos\Dev\CsBot`)
- **Plataforma Alvo**: Google Antigravity `2.29.0` / CLI `agy 1.0.13`
- **Classificação de Natureza dos Dados**: `REAL` (arquivos materializados e verificados no sistema de arquivos local)
- **Status deRevisão**: `AGENT_REVIEWED` (`Customization Explorer`, `Skill Designer`, `Script Implementer`, `Adversarial Skill Reviewer`)
- **Comando Reprodutível de Verificação de Hashes**:
  ```powershell
  Get-FileHash -Algorithm SHA256 AGENTS.md, .agents/skills.json, .agents/rules/*.md, .agents/skills/*/SKILL.md, .agents/skills/*/references/*.md, .agents/skills/*/scripts/*.py
  ```
- **Fórmula de Agregação de Integridade Estrutural**:
  $$\text{Conformidade de Tamanho} = \frac{\text{Arquivos com Tamanho} < 24.576\text{ bytes}}{\text{Total de Arquivos de Regras e Skills}} = \frac{33}{33} = 100.0\%$$

---

## 1. Camada de Regras de Governança (`AGENTS.md` e `.agents/rules/`)

As regras abaixo operam em modo `always_on` por descoberta hierárquica (*walk-up* da árvore de diretórios até a raiz `.git`). `AGENTS.md` não utiliza frontmatter YAML, conforme especificação oficial em `docs/rules.md`.

| ID da Regra | Caminho Relativo ao Workspace | Tamanho (Bytes) | Hash SHA-256 Completo (64 hex) | Natureza |
|---|---|---:|---|---|
| **Master `AGENTS.md`** | [AGENTS.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/AGENTS.md) | `6.740` | `dfc29fac7d3953f33c3ee3329d878a2f427d1da6268d88e5b928b338518694af` | `REAL` |
| `01-evidence-before-claims` | [01-evidence-before-claims.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/01-evidence-before-claims.md) | `379` | `04b3dc7b8a77e21eba24c9338c41329a532e10f7eca9de5bb2aabef1247c8824` | `REAL` |
| `02-no-test-contamination` | [02-no-test-contamination.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/02-no-test-contamination.md) | `292` | `62b5c724986e743024a5364c3b476211699cd2f93ef48c690750026d8cb7a31b` | `REAL` |
| `03-zero-support-is-na` | [03-zero-support-is-na.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/03-zero-support-is-na.md) | `237` | `06fbd734793bd771e6fd298abc53844b9ac470ba08f45f6406a26e73616fd6e2` | `REAL` |
| `04-synthetic-data-labeling` (`SYNTHETIC`/`SIMULATED`) | [04-synthetic-data-labeling.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/04-synthetic-data-labeling.md) | `347` | `9fe475f75a02df3199d1c85951a30f90602343ff753a7445e266f600c9d13873` | `REAL` |
| `05-human-review-integrity` | [05-human-review-integrity.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/05-human-review-integrity.md) | `296` | `992783e962f5db7a356d7fea7c6690b74193dfc2f8c5c787f90e75ca7eaa31b0` | `REAL` |
| `06-sensitive-artifact-protection` | [06-sensitive-artifact-protection.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/06-sensitive-artifact-protection.md) | `319` | `352d9ddfde8c23487bd02df0f3eb87a020ff7bcb6e5e587ce13a5cc55deb2289` | `REAL` |
| `07-independent-validation` | [07-independent-validation.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/07-independent-validation.md) | `222` | `1f28a65407d81a650d2b0a2c1499ec58bab1808b7cbe21e70f0438ae4a73aaca` | `REAL` |
| `08-no-automatic-phase-advance` | [08-no-automatic-phase-advance.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/rules/08-no-automatic-phase-advance.md) | `252` | `20c27df3a63d9e5d1e20c38db9fd2482b4b00e0c505c96c2879488878bc0f216` | `REAL` |
| **Manifesto de Skills** | [skills.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills.json) | `66` | `2f9471e01ffd7af746412d11494e0930a4d0ca96bd7d573214e645260fea3a31` | `REAL` |

---

## 2. Inventário das 6 Skills do Workspace (`.agents/skills/`)

Todas as 6 Skills estão instaladas em `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\skills\<skill-name>\` e registradas em `.agents/skills.json`. Nenhum dataset, checkpoint, DLL, modelo ou exemplo não utilizado foi incluído nas pastas das Skills.

### 2.1 `csbot-phase-gate`
- **Função**: Controlar entrada, execução e encerramento formal de fases do projeto CsBot, emitindo vereditos restritos a `PASS`, `CONDITIONAL` ou `FAIL` e exigindo autorização humana antes de avançar.
- **Entregáveis Gerados pela Skill**: `phase_input_snapshot.json`, `phase_requirement_matrix.md`, `phase_evidence_matrix.json`, `phase_gate_report.md`.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/SKILL.md) — `3.712 bytes` — SHA-256: `5fb7f048956ee0a924b4b3ca83290c94c24f0bad6a562b8b99d5d143b70c94cc`
  - [phase_gate_contract.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/references/phase_gate_contract.md) — `5.193 bytes` — SHA-256: `ece7c918c4c10d1d480b1031cc1693deac1112605beed90864d07764700a985b`
  - [run_phase_gate.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/scripts/run_phase_gate.py) — `17.712 bytes` — SHA-256: `0069c286ab7ff357b17f4f63d3fb507112a5121e2cba063cff4321ccd4838134`

### 2.2 `csbot-report-skeptic`
- **Função**: Auditar de forma cética e adversarial relatórios executivos e entregas de fase para detectar os 12 padrões de invalidação metodológica ou documental.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/SKILL.md) — `3.906 bytes` — SHA-256: `86a1bf22a91f9972e2283449e65d72efb9ba1e9dfc25b96b234835154713edf8`
  - [skeptic_audit_checklist.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/references/skeptic_audit_checklist.md) — `5.368 bytes` — SHA-256: `0e01db8d47d67a9437dc2318dea6821f2e8d74cc92d2d49a9df67cfffedca0ba`
  - [audit_executive_report.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py) — `20.425 bytes` — SHA-256: `b316b8a2eea5e243c0683192088078b715dda53e618beb66e8dd0349b2a74f62`

### 2.3 `csbot-dataset-forensics`
- **Função**: Auditar forensemente splits, leakage, Parquet, NPZ, proveniência, labels, contabilidade, sequências, rejeições e amostragem visual.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/SKILL.md) — `3.938 bytes` — SHA-256: `eef7b598b2f20e61128a119ae09546435cf81adaf0f8a89865329bc590523f01`
  - [dataset_forensics_protocol.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/references/dataset_forensics_protocol.md) — `4.185 bytes` — SHA-256: `6e20b2daf706d4cf84384ce1703fe0ee1b230b419fb7bc700dc616f63f067cf8`
  - [check_split_leakage.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/check_split_leakage.py) — `23.101 bytes` — SHA-256: `d29305f8852538ea826182295ed90d7b01ce5731df5be9383b5ec67cb5c16929`
  - [reconcile_dataset_counts.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/reconcile_dataset_counts.py) — `22.563 bytes` — SHA-256: `b7ffd2a9063fd1368578cbb10930c4428ad9a09d73e857a5291f4aa90926a687`
  - [audit_parquet_rows.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/audit_parquet_rows.py) — `16.800 bytes` — SHA-256: `59f92900b70f35a5f7155021933d1a3ab42dfc6faf433e808657e371c34393b5`
  - [verify_sample_provenance.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py) — `14.104 bytes` — SHA-256: `e6da72636731064ba84004a11f0d86198c417dd3c1e26a55081e4e28cf5b57b8`
  - [detect_templated_outputs.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/detect_templated_outputs.py) — `16.194 bytes` — SHA-256: `2069a7bd7fb10b73a2434347e3e0bd331432aa4ab06fed192a6ab6c643247663`
  - [audit_label_support.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/audit_label_support.py) — `20.171 bytes` — SHA-256: `2f4c90954d3055ace527d2400bd995fc2cf4339bfe05a2421efceafe8b921feb`

### 2.4 `csbot-model-validator`
- **Função**: Reproduzir deterministicamente a avaliação diretamente de checkpoints (`*.pt`) e arrays brutos (`.npz`), respeitando `model.eval()`, `torch.no_grad()`, `shuffle=False`, sem augmentation/teacher forcing e impondo `support=0 -> N/A`.
- **Entregáveis Gerados pela Skill**: `canonical_eval_manifest.json`, `canonical_metrics.json`, `confusion_counts.csv`, `confusion_normalized.csv`, `calibration.json`, `checkpoint_comparison.json`.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/SKILL.md) — `3.547 bytes` — SHA-256: `07ea2e077d8f6befd38482979002df8dfedbc65fb0bf39a3f3f4d49bf592f8d5`
  - [model_eval_invariants.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/references/model_eval_invariants.md) — `3.916 bytes` — SHA-256: `94d62eee156d7174b690b33b0246b33d7b395e83615fd1012c30e539ef62efe9`
  - [validate_model_canonical.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/scripts/validate_model_canonical.py) — `18.658 bytes` — SHA-256: `723e32394f7e81fd51e518801f1e541312936cfb3c3e84f91f9bd197a6b1242a`

### 2.5 `csbot-runtime-validation`
- **Função**: Padronizar build, testes, deploy, hashes, captura `!debug`, C4, economia, Jump, recovery, spots, adaptações e selamento da partida, proibindo simulação de runtime ou inferência de zero por ausência de telemetria.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/SKILL.md) — `3.698 bytes` — SHA-256: `44f5d324eb8a79fb20ccd37746c2c5b36ecc8c752d92379c1c322c023dc164ba`
  - [runtime_telemetry_contract.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/references/runtime_telemetry_contract.md) — `4.137 bytes` — SHA-256: `b2a6164d639b6aecfc820bd89fd101aee5e166e5fabab51d09cd44492aaa3e6d`
  - [verify_runtime_session.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py) — `9.749 bytes` — SHA-256: `fa0623a5552a7ab6f39c4e7633f8f33f0bf6b5832b3cf28cd5e71784e3c71106`

### 2.6 `csbot-graph-impact`
- **Função**: Integrar o grafo de conhecimento Graphify (`graphify-out/graph.json`) e o código C#/Python real ao planejamento de mudanças, mapeando 10 dimensões de impacto e os 5 grafos prioritários do CsBot.
- **Arquivos Componentes**:
  - [SKILL.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/SKILL.md) — `3.835 bytes` — SHA-256: `c4e9ff1d4f62a2eb8bb98c4493627ec589c238880a71e0a5758fa852dab62531`
  - [priority_graphs_catalog.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/references/priority_graphs_catalog.md) — `7.869 bytes` — SHA-256: `f181f4acbc266139c8a1742b8b0ca6e82da1f3163e95e4ef97ce267dae0d2007`
  - [analyze_graph_impact.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py) — `23.792 bytes` — SHA-256: `8f618ab32766d196495683ac551674a71cf0689c047b46a058d4616542f3aa7b`
