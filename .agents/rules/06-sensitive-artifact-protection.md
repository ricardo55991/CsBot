# Regra 06: Sensitive Artifact Protection (`06-sensitive-artifact-protection`)

Antes de criar nova versão, sobrescrever ou modificar qualquer artefato sensível:
- Modelos e pesos exportados (`*.onnx`, `*.pt`);
- Perfil tático de mapa (`src/CsBotManager/MapProfiles/*.json`);
- Arquivos de divisão de dados (`*split*.json`, `*split*.parquet`, `*split*.npz`);
- Manifests (`*manifest*.json`);
- Catálogos (`*catalog*.json`);
- Contratos de schema (`*contract*.json`);
- Checkpoints de treinamento;

**É obrigatório registrar previamente**:
1. **Hash SHA-256 anterior completo** (64 caracteres) verificado diretamente no disco;
2. **Caminho do backup** imutável criado antes da alteração;
3. **Diff planejado** exato;
4. **Procedimento de rollback** determinístico;
5. **Justificativa técnica** documentada.

> **Regra de Bloqueio**: O hook `protect-sensitive-files` intercepta e bloqueia modificações nesses alvos sem arquivo de autorização formal contendo esses 5 campos válidos.
