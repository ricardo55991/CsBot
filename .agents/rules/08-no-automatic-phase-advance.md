# Regra 08: No Automatic Phase Advance (`08-no-automatic-phase-advance`)

Nenhuma fase, subfase, retreinamento, exportação ou etapa de deploy pode ser iniciada imediatamente após o encerramento da anterior de maneira autônoma.

Ao emitir o veredito canônico:
- `PASS`
- `CONDITIONAL`
- `FAIL`

O assistente/agente DEVE **encerrar o turno de ferramentas imediatamente** e solicitar expressamente a aprovação e comando do usuário humano antes de executar qualquer passo da fase subsequente.
