# Regra 04: Synthetic Data Labeling (`04-synthetic-data-labeling`)

Todo dado, log, coordenada, vetor de histórico, mira geométrica, métrica ou artefato que seja sintético, simulado, templado, interpolado linearmente ou hardcoded deve ser explicitamente marcado com sua etiqueta de origem (`SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED`).

**É terminantemente proibido apresentá-lo como**:
- Telemetria de runtime real do servidor CS2 (`REAL`);
- Extração de demo profissional real;
- Avaliação canônica de modelo;
- Inspeção ou captura humana;
- Métrica observada em partida.

> **Tratamento de Padrões e Variância**:
> - A detecção estática de `np.linspace`, baixa variância (`std == 0`) ou passo regular em tensores emite status **`WARNING_REQUIRES_PROVENANCE_REVIEW`**, exigindo auditoria de proveniência.
> - O veredito **`FAIL`** ocorre obrigatoriamente quando o dado sintético/templado **não estiver rotulado explicitamente** (`UNLABELED_SYNTHETIC`) ou quando for apresentado falsamente como `REAL`.
> - Em tabelas de benchmark, métricas sobre tensores sintéticos devem exibir a etiqueta visual `[SYNTHETIC_FEATURE]`.
