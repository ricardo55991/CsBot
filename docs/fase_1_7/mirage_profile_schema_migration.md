# Guia de Migração de Schema de Spots — Mirage V2 (Fase 1.7)

> [!IMPORTANT]
> Este documento especifica o contrato uniforme de dados semânticos para os 45 spots do perfil de mapa `de_mirage`, eliminando ambiguidades e inferências baseadas em strings de nomes ou prefixos.

---

## 1. Justificativa da Migração

No schema original (V1 / V2 preliminar), propriedades essenciais de tomada de decisão tática e validação espacial sofriam de inconsistências:
- O time (`side`) vinha registrado como `"CT"` ou `"TR"`, ou inferido via prefixo de ID;
- O bombsite associado (`associated_bombsite`) estava ausente na maioria dos spots de hold ou inferido por substring de nome;
- O papel permitido (`allowed_roles`) não existia explicitamente no JSON de spots;
- A métrica de confiança (`confidence`) e o estágio de validação (`validation_status`) não eram persistidos no metadado.

O novo schema unificado estabelece 17 campos explícitos e enums tipados com validação estrita.

---

## 2. Especificação do Schema Unificado

Cada spot tático deve conter os seguintes campos:

```json
{
  "id": "ct_a_ticket_passive",
  "name": "Ticket / Cabine CT",
  "sector": "Bombsite A",
  "side": "CounterTerrorist",
  "associated_bombsite": "A",
  "usage": "Hold",
  "allowed_roles": [
    "AWPer",
    "Anchor",
    "Rotator"
  ],
  "x": -1011.5,
  "y": -2479.9,
  "z": -168.0,
  "pitch": 0.0,
  "yaw": 60.0,
  "recommended_stance": "PASSIVE_HOLD",
  "is_off_angle": false,
  "fallback_spot_id": "ct_spawn_safe",
  "confidence": "MEDIUM",
  "validation_status": "PENDING_HUMAN_REVIEW"
}
```

### 2.1 Enums Tipados e Valores Permitidos

1. **`side`**:
   - `CounterTerrorist`
   - `Terrorist`
   *(Aliases de leitura legados: `"CT"` mapeia para `CounterTerrorist`; `"TR"` mapeia para `Terrorist`)*

2. **`associated_bombsite`**:
   - `None` (ex: Spawns)
   - `A`
   - `B`
   - `Mid`
   - `Dynamic`

3. **`usage`**:
   - `Spawn`
   - `Staging`
   - `Execute`
   - `Hold`
   - `Fallback`
   - `Plant`
   - `Retake`
   - `Lurk`
   - `Cover`
   - `FlankWatch`
   - `Defuse`
   - `Save`

4. **`confidence`**:
   - `HIGH`
   - `MEDIUM`
   - `LOW`

5. **`validation_status`**:
   - `PROFESSIONAL_CLUSTER_VALIDATED`
   - `PIPELINE_GEOMETRY_VALIDATED`
   - `RUNTIME_LOCAL_VALIDATED`
   - `RUNTIME_OBSERVED`
   - `RUNTIME_NOT_OBSERVED`
   - `INSUFFICIENT_EVIDENCE`
   - `PENDING_HUMAN_REVIEW`
   - `APPROVED_BY_USER`
   - `REJECTED_BY_USER`

---

## 3. Tabela de Mapeamento Antigo → Novo

| Campo Antigo (V1/V2 Preliminar) | Tipo Antigo | Campo Novo (V2 Uniforme) | Tipo Novo | Estratégia de Migração |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | `id` | `string` | Preservado intacto |
| `name` | `string` | `name` | `string` | Preservado intacto |
| `sector` | `string` | `sector` | `string` | Preservado intacto |
| `side` | `"CT"` / `"TR"` | `side` | `enum SpotSide` | Mapeado explicitamente para `CounterTerrorist` / `Terrorist` |
| *(ausente em 35 spots)* | `null` | `associated_bombsite` | `enum SpotBombsite` | Definido explicitamente por setor e tática |
| *(ausente em 35 spots)* | `null` | `usage` | `enum SpotUsage` | Atribuído de acordo com a função espacial (`Hold`, `Staging`, etc.) |
| *(ausente)* | `null` | `allowed_roles` | `List<string>` | Lista de roles autorizados para o spot |
| `x`, `y`, `z` | `float` | `x`, `y`, `z` | `float` | Preservadas as coordenadas V2 homologadas |
| `pitch`, `yaw` | `float` | `pitch`, `yaw` | `float` | Preservados ângulos V2 |
| `recommended_stance` | `string` | `recommended_stance` | `enum EngagementStance` | Preservado |
| `is_off_angle` | `bool` | `is_off_angle` | `bool` | Preservado |
| `fallback_spot_id` | `string?` | `fallback_spot_id` | `string?` | Preservado |
| *(ausente)* | `null` | `confidence` | `enum SpotConfidence` | `HIGH`, `MEDIUM` ou `LOW` |
| *(ausente)* | `null` | `validation_status` | `enum SpotValidationStatus`| `RUNTIME_OBSERVED`, `PENDING_HUMAN_REVIEW`, etc. |

---

## 4. Regras de Compatibilidade no Runtime C#

Para evitar quebras em sistemas legados ou em plugins externos:
1. O deserializador JSON em `Models.cs` suporta tanto o formato novo quanto o formato antigo através de aliases ou converters flexíveis;
2. As propriedades `Side` e `AssociatedBombsite` mantêm propriedades de conveniência que respondem aos valores antigos (`"CT"`, `"TR"`);
3. Nenhuma propriedade existente foi renomeada ou teve seu tipo primitivo rompido;
4. O arquivo `de_mirage.json` canônico permanece intacto na baseline até o fechamento formal.
