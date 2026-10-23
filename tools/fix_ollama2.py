with open(r'src/CsBotManager/OllamaIglService.cs', 'rb') as f:
    data = f.read()

target = b'public TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager, string? reason = null)'
idx = data.find(target)
assert idx != -1, 'target not found'

# Replace everything from idx to end of method
method_code = '''public TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager, string? reason = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace("\\"", "\'").Replace("\\r", " ").Replace("\\n", " ");
        var plan = new TacticalPlan
        {
            TacticName = isCt ? "Defesa Padr\u00e3o 2-1-2" : (buyState == BuyState.FORCE_BUY ? "Rush B com Smoke Janela" : "Execu\u00e7\u00e3o A com Dom\u00ednio Pal\u00e1cio"),
            TacticSummary = isCt ? "Marca\u00e7\u00e3o de posi\u00e7\u00f5es 2 A, 1 Meio e 2 B com paci\u00eancia e crossfire" : (buyState == BuyState.FORCE_BUY ? "Entrada r\u00e1pida na B explorando o apartamento" : "Staging controlado no pal\u00e1cio e rampa A com utilit\u00e1rias"),
            RoundTempo = (isCt || buyState != BuyState.FORCE_BUY) ? RoundTempo.SLOW_DEFAULT : RoundTempo.FAST_CONTACT,
            StagingDurationSeconds = (isCt || buyState != BuyState.FORCE_BUY) ? 18.0f : 0.0f,
            RawJson = "{\\"fallback\\": true, \\"side\\": \\"" + (isCt ? "CT" : "TR") + "\\", \\"reason\\": \\"" + reasonClean + "\\"}"
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }
}
'''
method_bytes = method_code.replace('\n', '\r\n').encode('utf-8')

new_data = data[:idx] + method_bytes
with open(r'src/CsBotManager/OllamaIglService.cs', 'wb') as f:
    f.write(new_data)
print('Fixed GenerateDeterministicFallbackPlan successfully')
