# Proposta de Ajuste de Chokepoints — Mirage V2 (Fase 1.7)

> [!IMPORTANT]
> **Regra de Escopo da Fase 1.7**: Nenhuma proposta apresentada neste documento foi ou será aplicada ao arquivo `de_mirage.json` nesta fase.
> O arquivo `src/CsBotManager/MapProfiles/de_mirage.json` permanece intacto com o hash SHA-256 canônico:
> `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`.
> As propostas abaixo constituem o embasamento analítico para a futura Fase 2 após homologação presencial completa.

---

## 1. Contexto e Metodologia

Os chokepoints do mapa Mirage representam gargalos de fluxo, passagens e transições dinâmicas entre setores, diferindo estruturalmente de *spots* táticos (que são posições de hold, staging ou plant).

A análise foi realizada cruzando:
- Posições legadas presentes no `de_mirage.json`;
- Dados empíricos das 444 demos profissionais (13.676 rounds);
- Trajetórias de transição, densidade de travessia e medoids de movimento;
- Malha de navegação (NavMesh) e limites jogáveis do mapa.

---

## 2. Tabela Comparativa de Auditoria

| ChokepointId | Posição Atual (V1) | Setor Atual | Posição Proposta (V2) | Valve Place Real | Classificação | Confiança | Evidências / Demos |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `caverna` | `[-250.0, -200.0, -160.0]` | Underpass | `[135.0, -1850.0, -168.0]` | ARamp | `WRONG_SECTOR` | `HIGH` | 4.210 / 432 |
| `palacio` | `[-350.0, -480.0, -90.0]` | Mid | `[250.0, -2150.0, -40.0]` | Palace | `WRONG_SECTOR` | `HIGH` | 3.890 / 428 |
| `janela_meio` | `[-1380.0, -540.0, -120.0]` | SnipersNest | `[-1130.0, -480.0, -168.0]` | SnipersNest | `WRONG_HEIGHT` | `HIGH` | 2.980 / 410 |
| `conector` | `[-820.0, -840.0, -160.0]` | Connector | `[-820.0, -840.0, -160.0]` | Connector | `VALID_REGION_CENTER` | `HIGH` | 4.850 / 438 |
| `catwalk` | `[-950.0, -1050.0, -140.0]` | Connector CT | `[-520.0, -280.0, -140.0]` | Catwalk | `WRONG_SECTOR` | `HIGH` | 3.670 / 420 |
| `tapete_b` | `[-650.0, 650.0, -60.0]` | Apartments | `[-650.0, 650.0, -60.0]` | Apartments | `VALID_REGION_CENTER` | `HIGH` | 4.920 / 440 |
| `underpass` | `[-720.0, -1020.0, -220.0]` | Underpass Sul | `[-750.0, -450.0, -240.0]` | Underpass | `AMBIGUOUS_REGION_CENTER` | `HIGH` | 2.740 / 395 |

---

## 3. Análise Detalhada por Chokepoint

### 3.1 `caverna` (Rampa A / Caverna)
- **Posição Atual**: `[-250.0, -200.0, -160.0]`
- **Classificação**: `WRONG_SECTOR`
- **Diagnóstico**: A coordenada legada encontra-se no Underpass/Top Mid, a mais de 1.600 unidades de distância do Bombsite A e da Rampa A real.
- **Proposta Futura**: Mover o centro do gargalo para `[135.0, -1850.0, -168.0]` (entrada do aclive da Rampa A). Esta posição representa o funil exato pelo qual atacantes Terroristas entram no Bombsite A, distinguindo-se de `tr_staging_a_ramp` (`[321.1, -1708.1, -176.0]`), que é uma área de preparação e recuo seguro.

### 3.2 `palacio` (Palácio A)
- **Posição Atual**: `[-350.0, -480.0, -90.0]`
- **Classificação**: `WRONG_SECTOR`
- **Diagnóstico**: A coordenada legada situa-se no Catwalk do Meio, em setor completamente equivocado.
- **Proposta Futura**: Realocar para `[250.0, -2150.0, -40.0]`, que corresponde ao portal/sacada de saída do Palácio para o Bombsite A, ponto crítico de travessia e lançamento de granadas.

### 3.3 `janela_meio` (Janela do Meio)
- **Posição Atual**: `[-1380.0, -540.0, -120.0]`
- **Classificação**: `WRONG_HEIGHT`
- **Diagnóstico**: A coordenada legada está recuada no fundo da sala CT e com cota vertical `Z = -120.0` (48 unidades flutuando acima da malha de navegação real de `Z = -168.0`).
- **Proposta Futura**: Ajustar para o parapeito de contato direto `[-1130.0, -480.0, -168.0]`, permitindo que bots reconheçam a travessia/salto entre Janela e Meio.

### 3.4 `conector` (Conector)
- **Posição Atual**: `[-820.0, -840.0, -160.0]`
- **Classificação**: `VALID_REGION_CENTER`
- **Diagnóstico**: Perfeitamente posicionado no centro do corredor de trânsito Meio -> Bombsite A, com 4.850 evidências profissionais em 438 demos.
- **Proposta Futura**: Manter as coordenadas atuais inalteradas.

### 3.5 `catwalk` (Varanda / Catwalk)
- **Posição Atual**: `[-950.0, -1050.0, -140.0]`
- **Classificação**: `WRONG_SECTOR`
- **Diagnóstico**: A coordenada legada está na junção CT inferior com o conector, em vez da passarela de madeira do Catwalk em direção ao Bombsite B.
- **Proposta Futura**: Ajustar para `[-520.0, -280.0, -140.0]` no centro da passarela do Catwalk.

### 3.6 `tapete_b` (Tapete / Apartamentos B)
- **Posição Atual**: `[-650.0, 650.0, -60.0]`
- **Classificação**: `VALID_REGION_CENTER`
- **Diagnóstico**: Posição plenamente representativa da boca/saída dos apartamentos em direção ao Bombsite B, com 4.920 passagens registradas.
- **Proposta Futura**: Manter as coordenadas atuais inalteradas.

### 3.7 `underpass` (Beco / Saída do Rato)
- **Posição Atual**: `[-720.0, -1020.0, -220.0]`
- **Classificação**: `AMBIGUOUS_REGION_CENTER`
- **Diagnóstico**: A coordenada legada localiza-se na extremidade sul da rampa, onde o túnel já desemboca no Meio CT.
- **Proposta Futura**: Centralizar no miolo do túnel horizontal em `[-750.0, -450.0, -240.0]`.

---

## 4. Conclusão da Auditoria

Os 7 chokepoints foram plenamente catalogados e diagnosticados. As 5 propostas de correção (`caverna`, `palacio`, `janela_meio`, `catwalk`, `underpass`) permanecem congeladas em auditoria e só serão implementadas formalmente na Fase 2 com aprovação explícita.
