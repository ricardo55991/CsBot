using System.Net.Http.Json;
using System.Text.Json;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class OllamaIglService
{
    private readonly HttpClient _httpClient;
    private readonly List<RoundHistoryItem> _history = new();
    private readonly object _historyLock = new();
    private const string OllamaEndpoint = "http://127.0.0.1:11434/api/generate";

    public OllamaIglService()
    {
        _httpClient = new HttpClient
        {
            Timeout = TimeSpan.FromMilliseconds(4500)
        };
    }

    public void RecordRoundResult(int roundNumber, CsTeam winner, string winReason, string? site, string tactic, RoundTempo tempo)
    {
        lock (_historyLock)
        {
            _history.Add(new RoundHistoryItem
            {
                RoundNumber = roundNumber,
                Winner = winner,
                WinReason = winReason,
                PlantedSite = site,
                TacticUsed = tactic,
                TempoUsed = tempo
            });

            if (_history.Count > 5)
            {
                _history.RemoveAt(0);
            }
        }
    }

    public async Task<TacticalPlan> GetTacticalDecisionAsync(
        string map,
        CsTeam team,
        BuyState buyState,
        int roundNumber,
        int avgMoney,
        string? customPlayerCall,
        bool isRejection,
        MapProfileManager? mapProfileManager = null,
        CancellationToken cancellationToken = default)
    {
        List<RoundHistoryItem> historySnapshot;
        bool wasLastRoundFastContact;
        lock (_historyLock)
        {
            historySnapshot = _history.ToList();
            wasLastRoundFastContact = historySnapshot.LastOrDefault()?.TempoUsed == RoundTempo.FAST_CONTACT;
        }

        try
        {
            bool isCt = team == CsTeam.CounterTerrorist;
            string side = isCt ? "Counter-Terrorist" : "Terrorist";
            string teamTag = isCt ? "CT" : "TR";

            string historySummary = historySnapshot.Count > 0
                ? string.Join("; ", historySnapshot.Select(h => $"R{h.RoundNumber}: Winner={h.Winner}, Ritmo={h.TempoUsed}, Tactic={h.TacticUsed}"))
                : "Primeiro round ou sem histórico recente.";

            string pacingRule = wasLastRoundFastContact
                ? "REGRA DE CADÊNCIA OBRIGATÓRIA: O último round foi rush/contato rápido. É PROIBIDO escolher FAST_CONTACT! Escolha SLOW_DEFAULT (15-22s de staging) ou TIMED_EXECUTE."
                : "Ritmos permitidos: SLOW_DEFAULT, POKE_AND_ROTATE, TIMED_EXECUTE, FAST_CONTACT.";

            string validSpotsPrompt = "";
            if (mapProfileManager != null)
            {
                var teamSpots = mapProfileManager.GetSpotsForTeam(teamTag);
                if (teamSpots.Count > 0)
                {
                    validSpotsPrompt = $"- SPOTS VÁLIDOS PERMITIDOS PARA ESTE TIME ({teamTag}) - Escolha staging_spot_id e execute_spot_id APENAS destes IDs:\n" +
                        string.Join(", ", teamSpots.Select(s => $"{s.Id} ({s.Sector})"));
                }
            }

            string jsonExample = isCt
                ? @"{
  ""tactic_name"": ""Defesa Posicional 2-1-2"",
  ""tactic_summary"": ""Controle de meio e crossfire nos dois bombsites"",
  ""round_tempo"": ""SLOW_DEFAULT"",
  ""staging_duration_seconds"": 18.0,
  ""bot_orders"": {
    ""bot_awper"": {
      ""target_area"": ""Mid Window"",
      ""role_action"": ""Hold long angle"",
      ""staging_spot_id"": ""ct_mid_window_deep_awp"",
      ""execute_spot_id"": ""ct_mid_window_crouch"",
      ""stance"": ""PASSIVE_HOLD"",
      ""fallback_spot_id"": ""ct_jungle_safe"",
      ""required_utilities"": [""smoke""],
      ""aggression_level"": ""medium""
    },
    ""bot_entry"": {
      ""target_area"": ""Bombsite A"",
      ""role_action"": ""Aggressive poke under palace"",
      ""staging_spot_id"": ""ct_a_palace_close_poke"",
      ""execute_spot_id"": ""ct_a_stairs_cross"",
      ""stance"": ""AGGRESSIVE_POKE"",
      ""fallback_spot_id"": ""ct_a_firebox_oneanddone"",
      ""required_utilities"": [""flash""],
      ""aggression_level"": ""high""
    },
    ""bot_rotator"": {
      ""target_area"": ""Connector"",
      ""role_action"": ""Mid support and fast rotate"",
      ""staging_spot_id"": ""ct_mid_connector_headshot"",
      ""execute_spot_id"": ""ct_a_stairs_cross"",
      ""stance"": ""JIGGLE_INFO"",
      ""fallback_spot_id"": ""ct_a_stairs_cross"",
      ""required_utilities"": [""hegrenade""],
      ""aggression_level"": ""medium""
    },
    ""bot_anchor"": {
      ""target_area"": ""Bombsite B"",
      ""role_action"": ""Solo anchor and van jiggle"",
      ""staging_spot_id"": ""ct_b_van_peek"",
      ""execute_spot_id"": ""ct_b_site_default_crouch"",
      ""stance"": ""JIGGLE_INFO"",
      ""fallback_spot_id"": ""ct_b_bench_deep"",
      ""required_utilities"": [""molotov""],
      ""aggression_level"": ""low""
    }
  }
}"
                : @"{
  ""tactic_name"": ""Execução A com Domínio Palácio"",
  ""tactic_summary"": ""Staging calmo no telhado e rampa para entrada coordenada"",
  ""round_tempo"": ""SLOW_DEFAULT"",
  ""staging_duration_seconds"": 18.0,
  ""bot_orders"": {
    ""bot_awper"": {
      ""target_area"": ""Mid"",
      ""role_action"": ""Hold top mid line"",
      ""staging_spot_id"": ""tr_staging_top_mid_boxes"",
      ""execute_spot_id"": ""tr_exec_mid_connector_push"",
      ""stance"": ""PASSIVE_HOLD"",
      ""fallback_spot_id"": ""tr_staging_t_roof"",
      ""required_utilities"": [""smoke""],
      ""aggression_level"": ""medium""
    },
    ""bot_entry"": {
      ""target_area"": ""Palace"",
      ""role_action"": ""Entry on A site default"",
      ""staging_spot_id"": ""tr_staging_palace_room"",
      ""execute_spot_id"": ""tr_exec_a_site_default"",
      ""stance"": ""AGGRESSIVE_POKE"",
      ""fallback_spot_id"": ""tr_staging_a_ramp"",
      ""required_utilities"": [""flash""],
      ""aggression_level"": ""high""
    },
    ""bot_rotator"": {
      ""target_area"": ""Ramp A"",
      ""role_action"": ""Utility support on ramp"",
      ""staging_spot_id"": ""tr_staging_a_ramp"",
      ""execute_spot_id"": ""tr_exec_a_triple_clear"",
      ""stance"": ""JIGGLE_INFO"",
      ""fallback_spot_id"": ""tr_spawn_safe"",
      ""required_utilities"": [""hegrenade""],
      ""aggression_level"": ""medium""
    },
    ""bot_anchor"": {
      ""target_area"": ""Underpass"",
      ""role_action"": ""Watch flank from underpass"",
      ""staging_spot_id"": ""tr_staging_underpass_top"",
      ""execute_spot_id"": ""tr_exec_a_stairs_clear"",
      ""stance"": ""PASSIVE_HOLD"",
      ""fallback_spot_id"": ""tr_staging_t_roof"",
      ""required_utilities"": [""molotov""],
      ""aggression_level"": ""low""
    }
  }
}";

            string prompt = $@"
Você é o Capitão e Estrategista (IGL) no CS2.
Contexto do Round:
- Mapa: {map} | Lado: {side} | Round: {roundNumber}
- Economia: {buyState} (Média: ${avgMoney})
- Histórico: {historySummary}
- {pacingRule}
{validSpotsPrompt}
- Instrução do Humano: {(string.IsNullOrEmpty(customPlayerCall) ? (isRejection ? "Tática anterior rejeitada, proponha outra completamente diferente." : "Decida o melhor ritmo e plano tático.") : customPlayerCall)}

Responda APENAS um JSON válido seguindo esta estrutura exata:
{jsonExample}";

            var requestBody = new
            {
                model = "qwen2.5:3b",
                prompt = prompt,
                stream = false,
                format = "json",
                keep_alive = -1,
                options = new
                {
                    temperature = 0.4,
                    num_predict = 220
                }
            };

            var response = await _httpClient.PostAsJsonAsync(OllamaEndpoint, requestBody, cancellationToken);
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadFromJsonAsync<JsonElement>(cancellationToken: cancellationToken);
                if (content.TryGetProperty("response", out var rawJson))
                {
                    string jsonString = (rawJson.GetString() ?? string.Empty).Trim();
                    if (jsonString.StartsWith("```json", StringComparison.OrdinalIgnoreCase))
                    {
                        jsonString = jsonString.Substring(7);
                    }
                    else if (jsonString.StartsWith("```"))
                    {
                        jsonString = jsonString.Substring(3);
                    }
                    if (jsonString.EndsWith("```"))
                    {
                        jsonString = jsonString.Substring(0, jsonString.Length - 3);
                    }
                    jsonString = jsonString.Trim();
                    var parsed = JsonSerializer.Deserialize<TacticalPlan>(jsonString);
                    if (parsed != null && !string.IsNullOrEmpty(parsed.TacticName))
                    {
                        parsed.RawJson = jsonString;
                        parsed.IsCustomPlayerCall = !string.IsNullOrEmpty(customPlayerCall);

                        // Aplica a restrição de cadência estrita
                        if (wasLastRoundFastContact && parsed.RoundTempo == RoundTempo.FAST_CONTACT)
                        {
                            parsed.RoundTempo = RoundTempo.SLOW_DEFAULT;
                            parsed.StagingDurationSeconds = 18.0f;
                        }

                        EnsureValidBotOrders(parsed, team, mapProfileManager);
                        return parsed;
                    }
                }
            }
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception)
        {
            // Fallback determinístico
        }

        return GenerateDeterministicFallbackPlan(team, buyState, mapProfileManager);
    }

    private void EnsureValidBotOrders(TacticalPlan plan, CsTeam team, MapProfileManager? mapProfileManager)
    {
        string expectedSide = team == CsTeam.CounterTerrorist ? "CT" : "TR";

        var roles = new[] { BotRole.AWPer, BotRole.EntryFragger, BotRole.Rotator, BotRole.Anchor };
        foreach (var role in roles)
        {
            string key = RoleManager.GetOrderKey(role);
            if (!plan.BotOrders.TryGetValue(key, out var order))
            {
                order = new BotTacticalOrder
                {
                    TargetArea = role == BotRole.Anchor ? "Bombsite B" : "Bombsite A",
                    RoleAction = "Defensive hold"
                };
                plan.BotOrders[key] = order;
            }

            // Valida se o StagingSpotId é real e pertence ao time correto
            var stagingSpot = mapProfileManager?.GetSpotById(order.StagingSpotId);
            if (stagingSpot == null || (!stagingSpot.Side.Equals(expectedSide, StringComparison.OrdinalIgnoreCase) && !stagingSpot.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase)))
            {
                var fallbackSpot = mapProfileManager?.GetMatchingSpotForOrder(role, order.TargetArea, team, true);
                if (fallbackSpot != null)
                {
                    order.StagingSpotId = fallbackSpot.Id;
                    order.Stance = fallbackSpot.RecommendedStance;
                    order.FallbackSpotId = fallbackSpot.FallbackSpotId ?? order.FallbackSpotId;
                }
            }

            // Valida se o ExecuteSpotId é real
            var execSpot = mapProfileManager?.GetSpotById(order.ExecuteSpotId);
            if (execSpot == null)
            {
                var fallbackExec = mapProfileManager?.GetMatchingSpotForOrder(role, order.TargetArea, team, false);
                if (fallbackExec != null)
                {
                    order.ExecuteSpotId = fallbackExec.Id;
                }
            }

            if (string.IsNullOrEmpty(order.FallbackSpotId))
            {
                order.FallbackSpotId = expectedSide == "CT" ? "ct_spawn_safe" : "tr_spawn_safe";
            }
        }
    }

    private TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        var plan = new TacticalPlan
        {
            TacticName = isCt ? "Defesa Padrão 2-1-2" : (buyState == BuyState.FORCE_BUY ? "Rush B com Smoke Janela" : "Execução A com Domínio Palácio"),
            TacticSummary = isCt ? "Marcação de posições 2 A, 1 Meio e 2 B com paciência e crossfire" : (buyState == BuyState.FORCE_BUY ? "Entrada rápida na B explorando o apartamento" : "Staging controlado no palácio e rampa A com utilitárias"),
            RoundTempo = (isCt || buyState != BuyState.FORCE_BUY) ? RoundTempo.SLOW_DEFAULT : RoundTempo.FAST_CONTACT,
            StagingDurationSeconds = (isCt || buyState != BuyState.FORCE_BUY) ? 18.0f : 0.0f,
            RawJson = "{\"fallback\": true, \"side\": \"" + (isCt ? "CT" : "TR") + "\"}"
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }
}
