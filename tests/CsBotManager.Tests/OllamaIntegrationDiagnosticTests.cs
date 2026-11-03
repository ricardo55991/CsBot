using System.Net.Http.Json;
using System.Text.Json;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class OllamaIntegrationDiagnosticTests
{
    private const string OllamaBaseUrl = "http://127.0.0.1:11434";
    private readonly HttpClient _client = new() { Timeout = TimeSpan.FromSeconds(20.0) };

    private async Task<bool> IsOllamaRunningAsync()
    {
        try
        {
            var resp = await _client.GetAsync($"{OllamaBaseUrl}/api/tags");
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    [Fact]
    public async Task StepA_GetModelAvailabilityAndListing()
    {
        if (!await IsOllamaRunningAsync()) return; // Ignora graciosamente se daemon não estiver ativo em CI

        var response = await _client.GetAsync($"{OllamaBaseUrl}/api/tags");
        Assert.True(response.IsSuccessStatusCode, $"Ollama /api/tags retornou status HTTP {response.StatusCode}");

        var json = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.True(json.TryGetProperty("models", out var models), "Propriedade 'models' ausente no retorno de /api/tags");
        Assert.True(models.GetArrayLength() > 0, "Nenhum modelo instalado no Ollama");

        bool foundQwen = false;
        foreach (var m in models.EnumerateArray())
        {
            if (m.TryGetProperty("name", out var nameProp) && nameProp.GetString()?.Contains("qwen2.5:3b") == true)
            {
                foundQwen = true;
                break;
            }
        }
        Assert.True(foundQwen, "Modelo 'qwen2.5:3b' não encontrado na listagem do Ollama.");
    }

    [Fact]
    public async Task StepB_MinimalModelCallWarmup()
    {
        if (!await IsOllamaRunningAsync()) return;

        var igl = new OllamaIglService();
        bool ok = await igl.WarmUpModelAsync();
        Assert.True(ok, "Chamada mínima (WarmUpModelAsync) ao Ollama falhou.");
    }

    [Fact]
    public async Task StepC_SingleIglPayloadCall_ProducesValidOllamaPlan()
    {
        if (!await IsOllamaRunningAsync()) return;

        var igl = new OllamaIglService();
        var mapMgr = new MapProfileManager();

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        var plan = await igl.GetTacticalDecisionAsync(
            map: "de_mirage",
            team: CsTeam.CounterTerrorist,
            buyState: BuyState.FULL_BUY,
            roundNumber: 3,
            avgMoney: 4500,
            customPlayerCall: null,
            isRejection: false,
            mapProfileManager: mapMgr,
            cancellationToken: cts.Token);

        Assert.NotNull(plan);
        Assert.True(plan.Source == TacticalDecisionSource.OLLAMA, $"Decisão caiu em fallback: Source={plan.Source}, Reason={plan.FallbackReason}, ParseStatus={plan.ParseStatus}");
        Assert.False(plan.FallbackUsed, $"Decisão caiu em fallback: {plan.FallbackReason}");
        Assert.Equal("OK", plan.ParseStatus);
        Assert.False(string.IsNullOrWhiteSpace(plan.TacticName));
        Assert.True(plan.BotOrders.Count > 0, "BotOrders não deve estar vazio");
    }

    [Fact]
    public async Task StepD_And_StepE_ConcurrentCtAndTrDecisions_ValidatedWithRealParser()
    {
        if (!await IsOllamaRunningAsync()) return;

        var igl = new OllamaIglService();
        var mapMgr = new MapProfileManager();

        var ctEcon = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            RoundNumberInHalf = 4,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 4800
        };

        var trEcon = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            RoundNumberInHalf = 4,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 4200
        };

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        var (ctPlan, trPlan) = await igl.GetConcurrentRoundDecisionsAsync(
            map: "de_mirage",
            internalRoundId: 4,
            roundNumber: 4,
            ctEcon: ctEcon,
            trEcon: trEcon,
            mapProfileManager: mapMgr,
            outerToken: cts.Token);

        // Validação CT com parser real
        Assert.NotNull(ctPlan);
        Assert.True(ctPlan.Source == TacticalDecisionSource.UTILITY_AI_ENGINE || ctPlan.Source == TacticalDecisionSource.OLLAMA, $"CT caiu em fallback: Source={ctPlan.Source}, Reason={ctPlan.FallbackReason}, ParseStatus={ctPlan.ParseStatus}");
        Assert.False(ctPlan.FallbackUsed, $"CT Plan caiu em fallback: {ctPlan.FallbackReason}");
        Assert.Equal("OK", ctPlan.ParseStatus);
        Assert.False(string.IsNullOrWhiteSpace(ctPlan.TacticName));

        // Validação TR com parser real
        Assert.NotNull(trPlan);
        Assert.True(trPlan.Source == TacticalDecisionSource.UTILITY_AI_ENGINE || trPlan.Source == TacticalDecisionSource.OLLAMA, $"TR caiu em fallback: Source={trPlan.Source}, Reason={trPlan.FallbackReason}, ParseStatus={trPlan.ParseStatus}");
        Assert.False(trPlan.FallbackUsed, $"TR Plan caiu em fallback: {trPlan.FallbackReason}");
        Assert.Equal("OK", trPlan.ParseStatus);
        Assert.False(string.IsNullOrWhiteSpace(trPlan.TacticName));
    }
}
