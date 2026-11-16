# Matriz de Requisitos da Fase: `GOV-REAL-TEST`

| ID | Regra de Governança | Descrição | Status | Observações |
|---|---|---|---|---|
| `REQ-GOV-01` | `01-evidence-before-claims` | Snapshot de entrada possui hashes SHA-256 completos (64 chars) para todos os artefatos listados. | **PASS** | Total de arquivos verificados: 2 (ausentes: 0). |
| `REQ-GOV-06` | `06-sensitive-artifact-protection` | Nenhum artefato sensível modificado sem registro prévio de hash SHA-256. | **PASS** | Operação executada em modo somente leitura sobre os artefatos do workspace. |
| `REQ-GOV-08` | `08-no-automatic-phase-advance` | Bloqueio de avanço automático de fase ativo aguardando homologação humana. | **PASS** | Relatório final contém cláusula explícita de bloqueio de avanço automático. |
