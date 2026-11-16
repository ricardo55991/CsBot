# Contrato de Governança e Schemas do Phase Gate (`csbot-phase-gate`)

Este documento detalha os requisitos estruturais, invariantes de auditoria e schemas dos quatro artefatos obrigatórios exigidos pela Skill `csbot-phase-gate`.

---

## 1. Mapeamento das 8 Regras Inegociáveis (`AGENTS.md`)

| Código da Regra | Verificação Obrigatória no Phase Gate | Condição Imediata de `FAIL` |
| :--- | :--- | :--- |
| `01-evidence-before-claims` | Toda afirmação em relatório possui entrada em `phase_evidence_matrix.json` com `path` existente, `sha256` de 64 caracteres, `command`, `formula` e `data_nature`. | Afirmação baseada apenas em Markdown/PDF ou hash truncado/ausente. |
| `02-no-test-contamination` | Histórico de experimentos comprova que `Test` / `Holdout Final` não foi usado em escolha de época, checkpoint, hiperparâmetros, calibração, thresholds ou features. | Qualquer leitura do split `Test` para decisão de modelagem ou seleção de `best_checkpoint`. |
| `03-zero-support-is-na` | Todas as classes/setores/spots com `support = 0` exibem `N/A` em Recall, F1, Balanced Accuracy e linhas normalizadas da matriz de confusão. | Substituição de `0/0` por `0.0`, `0.0%`, `1.0` ou `100.0%`, ou cópia de amostras de `Validation` para `Test`. |
| `04-synthetic-data-labeling` | Todo dado não-real possui etiqueta explícita (`SIMULATED`, `TEMPLATED`, `SYNTHETIC`, `INFERRED`). | Dado sintético, interpolado ou hardcoded apresentado como telemetria `REAL` ou demo real. |
| `05-human-review-integrity` | Selos `APPROVED_BY_USER`, `REJECTED_BY_USER` e `HUMAN_CAPTURE_IN_GAME` possuem registro de interação direta do usuário humano. | Agente ou script emitindo selo de aprovação/captura humana em vez de `AGENT_REVIEWED` / `SCRIPT_CAPTURED`. |
| `06-sensitive-artifact-protection` | `phase_input_snapshot.json` contém hash SHA-256 prévio, caminho do backup imutável, diff planejado, rollback e justificativa antes de alterar artefatos sensíveis. | Sobrescrita de `*.onnx`, `*.pt`, `MapProfiles/*.json`, splits, manifests ou contratos sem backup e hash prévio. |
| `07-independent-validation` | Registro de execução separada entre agente implementador, Auditor de Reprodução, Auditor Adversarial (`csbot-report-skeptic`) e Success Auditor. | Auto-aprovação onde o mesmo agente implementa e assina isoladamente o veredito final. |
| `08-no-automatic-phase-advance` | O relatório finaliza com veredito (`PASS`, `CONDITIONAL` ou `FAIL`) e interrompe o fluxo aguardando comando humano. | Início automático da próxima fase, retreinamento ou deploy sem autorização explícita do usuário. |

---

## 2. Schemas Canônicos dos Artefatos

### 2.1 `phase_input_snapshot.json`
Registra o estado imutável antes do início das modificações da fase:

```json
{
  "phase_id": "phase_04_positioning_refinement",
  "timestamp_utc": "2026-11-07T16:00:00Z",
  "git_commit": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  "git_dirty": false,
  "authorized_scope": "Descrição exata do escopo autorizado pelo usuário",
  "sensitive_artifacts": [
    {
      "path": "src/CsBotManager/MapProfiles/de_mirage.json",
      "original_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "backup_path": "backups/phase_04/de_mirage.json.bak",
      "planned_diff_summary": "Ajuste de spots táticos no bombsite A",
      "rollback_procedure": " Copy-Item backups/phase_04/de_mirage.json.bak src/CsBotManager/MapProfiles/de_mirage.json -Force",
      "technical_justification": "Correção de colisão estática identificada em telemetria real"
    }
  ]
}
```

### 2.2 `phase_requirement_matrix.md`
Tabela Markdown estruturada contendo:
- `Req ID` (ex: `REQ-01`)
- `Descrição do Requisito`
- `Regra AGENTS.md Associada`
- `Critério de Aceite Quantitativo/Verificável`
- `Status` (`PASS`, `CONDITIONAL`, `FAIL`)
- `ID da Evidência` (apontando para `phase_evidence_matrix.json`)

### 2.3 `phase_evidence_matrix.json`
Lista de evidências brutas verificáveis:

```json
{
  "phase_id": "phase_04_positioning_refinement",
  "evidences": [
    {
      "evidence_id": "EVID-01",
      "requirement_id": "REQ-01",
      "artifact_path": "artifacts/eval/canonical_metrics.json",
      "sha256": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
      "reproducible_command": "python .agents/skills/csbot-model-validator/scripts/validate_model_canonical.py --checkpoint-path models/pos.pt --metrics-input-json artifacts/eval/raw_eval_inputs.json --split-name val --output-dir artifacts/eval/val",
      "aggregation_formula": "sum(correct_valid_tokens) / count(valid_tokens_with_support_gt_0)",
      "data_nature": "REAL",
      "review_stamp": "AGENT_REVIEWED"
    }
  ]
}
```

### 2.4 `phase_gate_report.md`
Estrutura obrigatória do relatório de fechamento:
1. **Resumo Executivo e Veredito Formal** (`PASS`, `CONDITIONAL` ou `FAIL`)
2. **Tabela de Conformidade `AGENTS.md` (`01` a `08`)**
3. **Parecer da Validação Independente** (Reprodução + `csbot-report-skeptic` + Success Auditor)
4. **Links para Artefatos Brutos e Hashes SHA-256**
5. **Declaração de Parada Obrigatória (`08-no-automatic-phase-advance`)**
