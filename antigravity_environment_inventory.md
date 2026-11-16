# Inventário do Ambiente Antigravity e Workspace CsBot

Data da Coleta: 2026-11-07  
Workspace Analisado: `C:\Users\ricar\OneDrive\Documentos\Dev\CsBot`  
Ambiente Operacional: Windows 11 (Host: PC / OneDrive Dev)

---

## 1. Versão Instalada do Antigravity

- **Produto**: Google Antigravity
- **ProductVersion**: `2.29.0` (FileVersion: `2.29.0.0`)
- **Electron Version**: `44.5.1`
- **Copyright**: © 2026 Google
- **Executável Principal**: `C:\Users\ricar\AppData\Local\Programs\Antigravity\Antigravity.exe`
- **Language Server**: `C:\Users\ricar\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe`
- **CLI (`agy`) Version**: `1.0.13`
  - Binário CLI: `C:\Users\ricar\AppData\Local\agy\bin\agy.exe`

---

## 2. Edição Atual em Execução

- **Edição em Execução Ativa**: **Antigravity 2.0 (App Desktop / Electron)**
  - Processo ativo em primeiro plano: `Antigravity.exe` (PIDs: 3300, 6368, 8432, 12000, 12332, 14764, 16072).
  - Servidor de linguagem ativo: `language_server.exe` (PID: 18192).
  - Diretório de dados da aplicação (`App Data Directory`): `C:\Users\ricar\.gemini\antigravity`.
- **Edição CLI Integrada**: **Antigravity CLI (`agy`)** disponível globalmente no PATH em `C:\Users\ricar\AppData\Local\agy\bin\agy.exe`.
- **Edição IDE**: Suporte a Antigravity IDE (baseado no VS Code) configurado com perfil em `~/.gemini/antigravity-ide/`.

---

## 3. Diretórios de Customizações Globais

Diretório Raiz Global: `C:\Users\ricar\.gemini\config\` (`~/.gemini/config/`)

Estrutura Existente no Disco:
```text
C:\Users\ricar\.gemini\config\
├── GEMINI.md                    # Regras globais (Idioma, Compiler-Driven Dev, Graphify SOP)
├── config.json                  # Configurações de plugins, permissões e políticas
├── mcp_config.json              # Configuração global de servidores MCP
├── plugins\                     # Plugins globais instalados
│   ├── chrome-devtools-plugin\
│   ├── google-antigravity-sdk\
│   └── modern-web-guidance-plugin\
├── skills\                      # Skills globais instaladas
│   └── graphify\                # Knowledge Graph & Community Detection
├── sidecars\                    # Sidecars globais
└── projects\                    # Metadados e snapshots por projeto
```

Diretório de Customizações Nativas (Built-in Bundled):
`C:\Users\ricar\.gemini\antigravity\builtin\skills\`
- `agy-customizations`
- `antigravity_guide`
- `automation`
- `generative_ui`
- `migrate-workflows`
- `permissioned-github`
- `plugin`
- `run-workflow`
- `ui-plugin-navigation`

---

## 4. Diretório de Customizações do Workspace CsBot

- **Raiz do Repositório**: `C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\`
- **Controle de Versão**: Git ativo (`.git` detectado na raiz)
- **Diretório Canônico de Customizações do Workspace**:
  - Caminho padrão: `C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\`
  - Aliases suportados pelo motor: `.agent\`, `_agents\`, `_agent\`
- **Status Atual no Workspace**: **Inexistente / Não Configurado**
  - Não há diretório `.agents/` criado.
  - Não há arquivos `GEMINI.md` ou `AGENTS.md` na raiz do workspace.
  - Não há `hooks.json`, `skills.json`, `plugins.json` ou `mcp_config.json` no workspace.
  - Todas as regras ativas no momento provêm exclusivamente do nível global (`~/.gemini/config/GEMINI.md` e `~/.gemini/GEMINI.md`).

---

## 5. Regras Globais Ativas Detectadas

As seguintes diretrizes globais foram extraídas de `~/.gemini/config/GEMINI.md` e estão sendo respeitadas em todas as sessões:
1. **Idioma**: Português Brasileiro obrigatório.
2. **Compiler-Driven Development (CDD)**: Nenhuma tarefa pode ser entregue sem compilar/testar o código autonomamente.
3. **Graphify Initialization SOP**: Inicialização do grafo e modo watch para novos workspaces.
