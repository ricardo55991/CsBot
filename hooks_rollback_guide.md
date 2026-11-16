# Guia Operacional de Controle, Modo Audit-Only e Rollback dos Hooks (`hooks_rollback_guide.md`)

- **Data de Geração**: `2026-11-07`
- **Escopo**: `.agents/hooks.json` e `.agents/hooks/` no workspace `CsBot`
- **Classificação de Natureza dos Dados**: `REAL`
- **Status de Revisão**: `AGENT_REVIEWED`

---

## 1. Como Alternar Entre `blocking` e `audit-only` (Sem Desinstalar Hooks)

Os 5 hooks leem seu modo de operação a partir do arquivo [`.agents/hooks/hook_mode.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/hook_mode.json) (ou da variável de ambiente `CSBOT_HOOK_MODE`).

### 1.1 Mudar para `audit-only` (Registra violações em `.agents/audit/hooks_audit.jsonl`, mas nunca bloqueia)
Execute no PowerShell na raiz do repositório:
```powershell
Set-Content -Path ".agents/hooks/hook_mode.json" -Value '{"mode": "audit-only", "updated_at": "2026-11-07T16:50:00Z", "reason": "Manutencao ou diagnostico"}' -Encoding UTF8
```

### 1.2 Voltar para `blocking` (Modo de Proteção Ativa Padrão)
```powershell
Set-Content -Path ".agents/hooks/hook_mode.json" -Value '{"mode": "blocking", "updated_at": "2026-11-07T16:50:00Z", "reason": "Governanca ativa"}' -Encoding UTF8
```

---

## 2. Como Desabilitar Individualmente um Hook em `.agents/hooks.json`

O schema nativo do Antigravity `2.29.0` (`docs/hooks.md`) suporta a propriedade `"enabled": false` no nível superior de cada hook nomeado em [`.agents/hooks.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks.json):

```json
{
  "pre-training-gate": {
    "enabled": false,
    "PreToolUse": [ ... ]
  }
}
```

Para desabilitar um único hook via PowerShell:
```powershell
python -c "import json, pathlib; p = pathlib.Path('.agents/hooks.json'); d = json.loads(p.read_text('utf-8')); d['stop-condition-evidence-gate']['enabled'] = False; p.write_text(json.dumps(d, indent=2), 'utf-8')"
```

---

## 3. Procedimento de Rollback Completo (Desativação Total dos Hooks do Workspace)

Caso seja necessário desativar todos os hooks do workspace imediatamente sem apagar os scripts de auditoria:

### Opção A — Desativação Rápida por Renomeação de `.agents/hooks.json`
```powershell
Move-Item -Path ".agents/hooks.json" -Destination ".agents/hooks.json.disabled" -Force
```
*(O Antigravity deixa de disparar qualquer hook imediatamente no próximo passo, preservando todos os scripts em `.agents/hooks/` e logs em `.agents/audit/`).*

Para restaurar:
```powershell
Move-Item -Path ".agents/hooks.json.disabled" -Destination ".agents/hooks.json" -Force
```

### Opção B — Restauração a partir da Cópia de Referência (`hooks_config.json`)
Se `.agents/hooks.json` for editado incorretamente, restaure a cópia canônica validada:
```powershell
Copy-Item -Path "hooks_config.json" -Destination ".agents/hooks.json" -Force
```

---

## 4. Como Autorizar Legitimamente a Modificação de um Artefato Sensível (`Hook A`)

Quando uma fase autorizada precisar atualizar um arquivo protegido (`*.onnx`, `*.pt`, `de_mirage.json`, `*split*.json`, `*manifest*.json`, `*contract*.json`, `*catalog*.json`):

1. Crie o backup imutável e calcule o SHA-256 completo (64 caracteres hexadecimais) do arquivo atual:
   ```powershell
   Copy-Item "src/CsBotManager/MapProfiles/de_mirage.json" "src/CsBotManager/MapProfiles/backups/de_mirage.backup.json"
   Get-FileHash -Algorithm SHA256 "src/CsBotManager/MapProfiles/de_mirage.json"
   ```
2. Preencha o manifesto JSON de autorização `sensitive_file_authorization` (em `.agents/audit/`) com os 5 campos obrigatórios:
   ```json
   {
     "target_file": "src/CsBotManager/MapProfiles/de_mirage.json",
     "backup_path": "src/CsBotManager/MapProfiles/backups/de_mirage.backup.json",
     "previous_sha256": "<64_CARACTERES_HEX_DO_ARQUIVO_ATUAL>",
     "planned_diff": "Descrição objetiva da alteração autorizada",
     "rollback_command": "Copy-Item src/CsBotManager/MapProfiles/backups/de_mirage.backup.json src/CsBotManager/MapProfiles/de_mirage.json -Force",
     "approved_phase": "Fase_Autorizada_Pelo_Usuario"
   }
   ```
3. Realize a modificação autorizada.
