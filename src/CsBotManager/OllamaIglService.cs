using System.Diagnostics;
using System.Net.Http.Json;
using System.Text.Json;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class IglCallTelemetry
{
    public string DecisionId { get; set; } = string.Empty;
    public string Side { get; set; } = string.Empty;
    public string Endpoint { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public DateTime RequestStartUtc { get; set; }
    public float ConnectMs { get; set; }
    public float FirstByteMs { get; set; }
    public float TotalMs { get; set; }
    public int HttpStatus { get; set; }
    public long ResponseBytes { get; set; }
    public bool Cancelled { get; set; }
    public string CancellationSource { get; set; } = "NONE";
    public string TimeoutSource { get; set; } = "NONE";
    public string ExceptionType { get; set; } = "NONE";
    public string ExceptionMessage { get; set; } = "NONE";
    public string ParseResult { get; set; } = "NONE";
    public string FallbackReason { get; set; } = "NONE";

    public string ToLogString()
    {
        return $"[IGL_CALL_TELEMETRY] decisionId={DecisionId} side={Side} endpoint={Endpoint} model={Model} requestStartUtc={RequestStartUtc:o} connectMs={ConnectMs:F1} firstByteMs={FirstByteMs:F1} totalMs={TotalMs:F1} httpStatus={HttpStatus} responseBytes={ResponseBytes} cancelled={Cancelled} cancellationSource={CancellationSource} timeoutSource={TimeoutSource} exceptionType={ExceptionType} exceptionMessage={ExceptionMessage} parseResult={ParseResult} fallbackReason={FallbackReason}";
    }
}

public class CandidateTacticScore
{
    public string TacticName { get; set; } = string.Empty;
    public string Summary { get; set; } = string.Empty;
    public RoundTempo RecommendedTempo { get; set; } = RoundTempo.SLOW_DEFAULT;
    public float RecommendedStagingSeconds { get; set; } = 16.0f;
    public float BaseContextualScore { get; set; } = 100.0f;
    public float RepetitionPenalty { get; set; } = 0.0f;
    public float FinalScore => BaseContextualScore - RepetitionPenalty;
    public string Rationale { get; set; } = string.Empty;
}

public class OllamaIglService
{
    private readonly HttpClient _httpClient;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        AllowTrailingCommas = true,
        ReadCommentHandling = JsonCommentHandling.Skip
    };

    private readonly List<RoundHistoryItem> _history = new();
    private readonly Dictionary<CsTeam, List<string>> _teamTacticHistory = new()
    {
        { CsTeam.CounterTerrorist, new List<string>() },
        { CsTeam.Terrorist, new List<string>() }
    };
    private readonly Dictionary<string, TacticalPlan> _decisionCache = new(StringComparer.OrdinalIgnoreCase);
    private readonly object _historyLock = new();
    private const string OllamaEndpoint = "http://127.0.0.1:11434/api/generate";

    public OllamaIglService()
    {
        _httpClient = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(15.0)
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

            if (_history.Count > 8)
            {
                _history.RemoveAt(0);
            }
        }
    }

    public void RecordTeamTacticUsed(CsTeam team, string tacticName)
    {
        if (string.IsNullOrWhiteSpace(tacticName)) return;
        lock (_historyLock)
        {
            if (!_teamTacticHistory.TryGetValue(team, out var list))
            {
                list = new List<string>();
                _teamTacticHistory[team] = list;
            }
            list.Add(tacticName.Trim());
            if (list.Count > 6)
            {
                list.RemoveAt(0);
            }
        }
    }

    public List<CandidateTacticScore> EvaluateCandidateTactics(
        CsTeam team,
        BuyState buyState,
        int roundNumber,
        int avgMoney,
        int lossStreak = 0,
        IReadOnlyList<string>? recentTeamTactics = null,
        string? lastBombSite = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        var recent = recentTeamTactics;
        if (recent == null)
        {
            lock (_historyLock)
            {
                recent = _teamTacticHistory.TryGetValue(team, out var list) ? list.ToList() : new List<string>();
            }
        }

        var candidates = new List<CandidateTacticScore>();

        if (isCt)
        {
            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Defesa Padrão 2-1-2 Equilibrada",
                Summary = "Cobertura equilibrada com 2 no A, AWPer na Janela, Conector/Short ativo e Âncora B",
                RecommendedTempo = RoundTempo.SLOW_DEFAULT,
                RecommendedStagingSeconds = 18.0f,
                BaseContextualScore = buyState == BuyState.FULL_BUY ? 82.0f : 72.0f,
                Rationale = "Boa cobertura base em Full Buy"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Domínio Agressivo Meio (Janela + Conector + Short)",
                Summary = "Pressão coordenada no Meio para negar splits e obter vantagem numérica cedo",
                RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
                RecommendedStagingSeconds = 8.0f,
                BaseContextualScore = (buyState == BuyState.FULL_BUY || buyState == BuyState.FORCE_BUY) ? 88.0f : 74.0f,
                Rationale = "Nega controle de Meio dos TRs e força execuções previsíveis pelas pontas"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Stack A & Retake B Preparado (3-1-1)",
                Summary = "Forte presença no Palácio/Rampa/Conector com âncora de informação no B",
                RecommendedTempo = RoundTempo.SLOW_DEFAULT,
                RecommendedStagingSeconds = 15.0f,
                BaseContextualScore = (string.Equals(lastBombSite, "A", StringComparison.OrdinalIgnoreCase) || lossStreak >= 1 || buyState == BuyState.HALF_BUY || buyState == BuyState.FORCE_BUY)
                    ? 91.0f : 80.0f,
                Rationale = "Reforça o Bomb A contra execuções repetidas ou maximiza trocas em economia pressionada"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Setup Anti-Split B & Controle Underpass (1-2-2)",
                Summary = "Reforço de Catwalk/Underpass e Van/Mercado para punir entradas no Bomb B",
                RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
                RecommendedStagingSeconds = 12.0f,
                BaseContextualScore = string.Equals(lastBombSite, "B", StringComparison.OrdinalIgnoreCase) ? 92.0f : 79.0f,
                Rationale = "Neutraliza pressão no Tapete B e pinças pelo L-B"
            });
        }
        else
        {
            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Execução A (Palácio + Rampa Sincronizados)",
                Summary = "Domínio de Palácio e Rampa A com smokes em Escadas/Jungle e entrada rápida para plant",
                RecommendedTempo = RoundTempo.TIMED_EXECUTE,
                RecommendedStagingSeconds = 14.0f,
                BaseContextualScore = buyState == BuyState.FULL_BUY ? 89.0f : 78.0f,
                Rationale = "Execução estruturada de alto impacto no Bomb A"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Split A (Top Mid + Conector + Palácio)",
                Summary = "Pinça coordenada dominando Meio/Conector com entrada simultânea pelo Palácio",
                RecommendedTempo = RoundTempo.SLOW_DEFAULT,
                RecommendedStagingSeconds = 16.0f,
                BaseContextualScore = (buyState == BuyState.FULL_BUY || avgMoney >= 4000) ? 91.0f : 75.0f,
                Rationale = "Quebra o crossfire CT no Bomb A atacando Conector e Palácio"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Execução B (Tapete / Apartamentos Rápido)",
                Summary = "Progressão pelo Tapete B com entrada explosiva sobre Van e Default B",
                RecommendedTempo = (buyState == BuyState.PISTOL_ROUND || buyState == BuyState.FORCE_BUY || buyState == BuyState.HALF_BUY)
                    ? RoundTempo.FAST_CONTACT : RoundTempo.TIMED_EXECUTE,
                RecommendedStagingSeconds = (buyState == BuyState.PISTOL_ROUND || buyState == BuyState.FORCE_BUY) ? 4.0f : 11.0f,
                BaseContextualScore = (buyState == BuyState.PISTOL_ROUND || buyState == BuyState.FORCE_BUY) ? 93.0f : 84.0f,
                Rationale = "Encurta distância contra rifles CTs e isola o âncora do Bomb B"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Split B (Domínio Meio + Catwalk / Short + Tapete)",
                Summary = "Controle de Top Mid e Short B combinado com pressão pelo Apartamento B",
                RecommendedTempo = RoundTempo.SLOW_DEFAULT,
                RecommendedStagingSeconds = 15.0f,
                BaseContextualScore = 86.0f,
                Rationale = "Cerca o Bomb B por dois ângulos (Short/L-B e Tapete)"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
                Summary = "Finta no Bomb A com utilitárias na Rampa/Palácio e invasão veloz pelo Tapete B",
                RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
                RecommendedStagingSeconds = 10.0f,
                BaseContextualScore = (string.Equals(lastBombSite, "A", StringComparison.OrdinalIgnoreCase) || lossStreak >= 1) ? 90.0f : 81.0f,
                Rationale = "Atrai a rotação CT para o Bomb A e invade o Bomb B desguarnecido"
            });

            candidates.Add(new CandidateTacticScore
            {
                TacticName = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
                Summary = "Finta no Bomb B pelo Tapete/Underpass chamando rotação CT e invasão pelo Palácio/Rampa A",
                RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
                RecommendedStagingSeconds = 12.0f,
                BaseContextualScore = (string.Equals(lastBombSite, "B", StringComparison.OrdinalIgnoreCase) || lossStreak >= 1) ? 90.0f : 80.0f,
                Rationale = "Provoca rotação CT para a Van/B e golpeia o Bomb A com defesa enfraquecida"
            });
        }

        // Bônus determinístico rotativo por round para garantir diversidade quando os scores base empatam
        for (int i = 0; i < candidates.Count; i++)
        {
            if ((roundNumber + (isCt ? 1 : 2)) % candidates.Count == i)
            {
                candidates[i].BaseContextualScore += 9.0f;
            }
        }

        // Penalidade de repetição configurável (Corrige Bug 5: viés de repetição de "Defesa Posicional 2-1-2")
        string? lastTactic = recent.Count > 0 ? recent[^1] : null;
        string? secondLastTactic = recent.Count > 1 ? recent[^2] : null;

        foreach (var candidate in candidates)
        {
            float penalty = 0.0f;
            if (!string.IsNullOrEmpty(lastTactic) && IsSimilarTacticName(candidate.TacticName, lastTactic))
            {
                penalty += Config.TacticRepetitionPenaltyScore;
            }
            if (!string.IsNullOrEmpty(secondLastTactic) && IsSimilarTacticName(candidate.TacticName, secondLastTactic))
            {
                penalty += Config.TacticRepetitionPenaltyScore * 0.65f;
            }
            candidate.RepetitionPenalty = penalty;
        }

        return candidates.OrderByDescending(c => c.FinalScore).ToList();
    }

    private static bool IsSimilarTacticName(string a, string b)
    {
        if (string.IsNullOrWhiteSpace(a) || string.IsNullOrWhiteSpace(b)) return false;
        string na = a.Trim().ToLowerInvariant();
        string nb = b.Trim().ToLowerInvariant();
        if (na == nb || na.Contains(nb) || nb.Contains(na)) return true;

        if ((na.Contains("2-1-2") && nb.Contains("2-1-2")) ||
            (na.Contains("avanço") && nb.Contains("avanço")) ||
            (na.Contains("domínio agressivo meio") && nb.Contains("meio")) ||
            (na.Contains("stack a") && nb.Contains("stack a")) ||
            (na.Contains("anti-split b") && nb.Contains("anti-split b")) ||
            (na.Contains("execução a") && nb.Contains("execução a")) ||
            (na.Contains("split a") && nb.Contains("split a")) ||
            (na.Contains("execução b") && nb.Contains("execução b")) ||
            (na.Contains("split b") && nb.Contains("split b")))
        {
            return true;
        }

        return false;
    }

    public async Task<bool> WarmUpModelAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var pingPayload = new
            {
                model = "qwen2.5:3b",
                prompt = "ok",
                stream = false,
                keep_alive = -1,
                options = new { num_predict = 1 }
            };
            var resp = await _httpClient.PostAsJsonAsync(OllamaEndpoint, pingPayload, cancellationToken);
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    public async Task<(TacticalPlan CtPlan, TacticalPlan TrPlan)> GetConcurrentRoundDecisionsAsync(
        string map,
        int internalRoundId,
        int roundNumber,
        TeamEconomySnapshot ctEcon,
        TeamEconomySnapshot trEcon,
        MapProfileManager? mapProfileManager = null,
        Func<int>? tickProvider = null,
        CancellationToken outerToken = default)
    {
        int startTick = tickProvider?.Invoke() ?? 0;

        // V4.2.1: Executa sequencialmente com timeout individual e desacoplado por time
        // Como o Ollama serializa requisições se num_parallel=1, a execução ordenada garante que a espera na fila de TR não consuma o timeout de 8500ms
        using var ctCts = CancellationTokenSource.CreateLinkedTokenSource(outerToken);
        ctCts.CancelAfter(Config.OllamaDecisionTimeoutMs);

        var ctPlan = await GetTacticalDecisionAsync(
            map,
            CsTeam.CounterTerrorist,
            ctEcon.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY ? ctEcon.FinalBuyState : ctEcon.PurchaseIntent,
            roundNumber,
            ctEcon.AverageCashBeforeBuy,
            customPlayerCall: null,
            isRejection: false,
            mapProfileManager: mapProfileManager,
            cancellationToken: ctCts.Token,
            internalRoundId: internalRoundId,
            requestedAtTick: startTick,
            tickProvider: tickProvider);

        using var trCts = CancellationTokenSource.CreateLinkedTokenSource(outerToken);
        trCts.CancelAfter(Config.OllamaDecisionTimeoutMs);

        var trPlan = await GetTacticalDecisionAsync(
            map,
            CsTeam.Terrorist,
            trEcon.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY ? trEcon.FinalBuyState : trEcon.PurchaseIntent,
            roundNumber,
            trEcon.AverageCashBeforeBuy,
            customPlayerCall: null,
            isRejection: false,
            mapProfileManager: mapProfileManager,
            cancellationToken: trCts.Token,
            internalRoundId: internalRoundId,
            requestedAtTick: startTick,
            tickProvider: tickProvider);

        return (ctPlan, trPlan);
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
        CancellationToken cancellationToken = default,
        int internalRoundId = 0,
        int requestedAtTick = 0,
        Func<int>? tickProvider = null)
    {
        var sw = Stopwatch.StartNew();
        bool isCt = team == CsTeam.CounterTerrorist;
        string teamTag = isCt ? "CT" : "TR";
        string decisionId = $"DEC-R{(internalRoundId > 0 ? internalRoundId : roundNumber):D2}-{teamTag}-{Guid.NewGuid().ToString("N")[..6].ToUpperInvariant()}";

        var callTelemetry = new IglCallTelemetry
        {
            DecisionId = decisionId,
            Side = teamTag,
            Endpoint = OllamaEndpoint,
            Model = "qwen2.5:3b",
            RequestStartUtc = DateTime.UtcNow
        };

        List<RoundHistoryItem> historySnapshot;
        List<string> recentTeamTactics;
        bool wasLastRoundFastContact;
        string? lastBombSite;
        int lossStreak = 0;

        lock (_historyLock)
        {
            historySnapshot = _history.ToList();
            wasLastRoundFastContact = historySnapshot.LastOrDefault()?.TempoUsed == RoundTempo.FAST_CONTACT;
            lastBombSite = historySnapshot.LastOrDefault(h => !string.IsNullOrEmpty(h.PlantedSite))?.PlantedSite;
            recentTeamTactics = _teamTacticHistory.TryGetValue(team, out var list) ? list.ToList() : new List<string>();

            for (int i = historySnapshot.Count - 1; i >= 0; i--)
            {
                if (historySnapshot[i].Winner != team && historySnapshot[i].Winner != CsTeam.None)
                    lossStreak++;
                else
                    break;
            }
        }

        var scoredCandidates = EvaluateCandidateTactics(
            team,
            buyState,
            roundNumber,
            avgMoney,
            lossStreak,
            recentTeamTactics,
            lastBombSite);

        var topCandidate = scoredCandidates.First();
        var secondCandidate = scoredCandidates.Count > 1 ? scoredCandidates[1] : topCandidate;

        try
        {
            string side = isCt ? "Counter-Terrorist" : "Terrorist";
            string historySummary = historySnapshot.Count > 0
                ? string.Join("; ", historySnapshot.Select(h => $"R{h.RoundNumber}: Winner={h.Winner}, Site={h.PlantedSite ?? "None"}, Tactic={h.TacticUsed}"))
                : "Primeiro round ou sem histórico recente.";

            string candidateMenu = string.Join("\n", scoredCandidates.Select((c, idx) =>
                $"  {idx + 1}. \"{c.TacticName}\" (Score Contextual: {c.FinalScore:F1} [Base {c.BaseContextualScore:F0} - Penalidade Repetição {c.RepetitionPenalty:F0}]) -> {c.Summary}"));

            string recentProhibition = recentTeamTactics.Count > 0
                ? $"PROIBIDO repetir literalmente a última tática usada ({string.Join(", ", recentTeamTactics.TakeLast(2))})! Priorize a candidata #1 (\"{topCandidate.TacticName}\") ou #2 (\"{secondCandidate.TacticName}\")."
                : $"Priorize a candidata de maior score contextual: \"{topCandidate.TacticName}\".";

            string pacingRule = wasLastRoundFastContact
                ? "REGRA DE CADÊNCIA OBRIGATÓRIA: O último round foi FAST_CONTACT. Escolha SLOW_DEFAULT ou TIMED_EXECUTE."
                : "Ritmos permitidos: SLOW_DEFAULT, POKE_AND_ROTATE, TIMED_EXECUTE, FAST_CONTACT.";

            // V4.2.1: Prompt conciso com bot_orders enxuto (garante resposta completa em <195 tokens em ~3.1s)
            var templatePlan = BuildPlanFromCandidate(topCandidate, team, mapProfileManager);
            var simplifiedOrders = templatePlan.BotOrders.ToDictionary(
                kvp => kvp.Key,
                kvp => new
                {
                    target_area = kvp.Value.TargetArea,
                    stance = kvp.Value.Stance.ToString()
                });

            string dynamicJsonTemplate = JsonSerializer.Serialize(new
            {
                tactic_name = templatePlan.TacticName,
                tactic_summary = templatePlan.TacticSummary,
                round_tempo = templatePlan.RoundTempo.ToString(),
                staging_duration_seconds = templatePlan.StagingDurationSeconds,
                bot_orders = simplifiedOrders
            }, new JsonSerializerOptions { WriteIndented = true });

            string prompt = $@"
Você é o Capitão e Estrategista (IGL) no CS2 ({side}).
Contexto do Round:
- Mapa: {map} | Lado: {side} | Round: {roundNumber}
- Economia: {buyState} (Média: ${avgMoney}, LossStreak: {lossStreak})
- Histórico Recente: {historySummary}
- Candidatas Táticas Avaliadas para este Round:
{candidateMenu}
- Diretriz de Diversidade: {recentProhibition}
- {pacingRule}
- Instrução do Humano: {(string.IsNullOrEmpty(customPlayerCall) ? (isRejection ? "Tática anterior rejeitada, proponha outra completamente diferente." : $"Estruture o plano detalhado para '{topCandidate.TacticName}' ou '{secondCandidate.TacticName}'.") : customPlayerCall)}

Responda APENAS um JSON válido seguindo esta estrutura:
{dynamicJsonTemplate}";

            var requestBody = new
            {
                model = "qwen2.5:3b",
                prompt = prompt,
                stream = false,
                format = "json",
                keep_alive = -1,
                options = new
                {
                    temperature = 0.25,
                    num_predict = 260
                }
            };

            var connectSw = Stopwatch.StartNew();
            using var reqMsg = new HttpRequestMessage(HttpMethod.Post, OllamaEndpoint)
            {
                Content = JsonContent.Create(requestBody)
            };

            var response = await _httpClient.SendAsync(reqMsg, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            connectSw.Stop();
            callTelemetry.ConnectMs = (float)connectSw.Elapsed.TotalMilliseconds;
            callTelemetry.HttpStatus = (int)response.StatusCode;

            var firstByteSw = Stopwatch.StartNew();
            using var respStream = await response.Content.ReadAsStreamAsync(cancellationToken);
            firstByteSw.Stop();
            callTelemetry.FirstByteMs = callTelemetry.ConnectMs + (float)firstByteSw.Elapsed.TotalMilliseconds;

            using var memStream = new MemoryStream();
            await respStream.CopyToAsync(memStream, cancellationToken);
            sw.Stop();
            callTelemetry.TotalMs = (float)sw.Elapsed.TotalMilliseconds;
            callTelemetry.ResponseBytes = memStream.Length;

            int completedTick = tickProvider?.Invoke() ?? requestedAtTick;

            if (response.IsSuccessStatusCode)
            {
                memStream.Position = 0;
                var content = await JsonSerializer.DeserializeAsync<JsonElement>(memStream, cancellationToken: cancellationToken);
                if (content.TryGetProperty("response", out var rawJson))
                {
                    string jsonString = CleanMarkdownJson(rawJson.GetString() ?? string.Empty);
                    var parsed = JsonSerializer.Deserialize<TacticalPlan>(jsonString, JsonOptions);
                    if (parsed != null && !string.IsNullOrEmpty(parsed.TacticName))
                    {
                        callTelemetry.ParseResult = "OK";
                        callTelemetry.FallbackReason = "NONE";
                        TelemetryLogger?.LogEvent("IGL_CALL_TELEMETRY", callTelemetry.ToLogString());

                        // Se o LLM ainda assim devolveu uma tática repetida penalizada quando não é call humana, promove o topCandidate!
                        string lastUsed = recentTeamTactics.LastOrDefault() ?? string.Empty;
                        bool repeatedLast = !string.IsNullOrEmpty(lastUsed) && IsSimilarTacticName(parsed.TacticName, lastUsed);
                        if (repeatedLast && string.IsNullOrEmpty(customPlayerCall))
                        {
                            var promoted = BuildPlanFromCandidate(topCandidate, team, mapProfileManager);
                            parsed.TacticName = promoted.TacticName;
                            parsed.TacticSummary = promoted.TacticSummary;
                            parsed.RoundTempo = promoted.RoundTempo;
                            parsed.StagingDurationSeconds = promoted.StagingDurationSeconds;
                            parsed.BotOrders = promoted.BotOrders;
                        }

                        if (wasLastRoundFastContact && parsed.RoundTempo == RoundTempo.FAST_CONTACT)
                        {
                            parsed.RoundTempo = RoundTempo.SLOW_DEFAULT;
                            parsed.StagingDurationSeconds = 16.0f;
                        }

                        EnsureValidBotOrders(parsed, team, mapProfileManager);
                        TacticalOrderMaterializer.ValidateAndRepairOrders(parsed, team, mapProfileManager, TelemetryLogger, decisionId);
                        PopulateAuditMetadata(
                            parsed,
                            decisionId,
                            internalRoundId > 0 ? internalRoundId : roundNumber,
                            team,
                            requestedAtTick,
                            completedTick,
                            sw.Elapsed.TotalMilliseconds,
                            TacticalDecisionSource.OLLAMA,
                            fallbackUsed: false,
                            fallbackReason: "NONE",
                            parseStatus: "OK",
                            modelResponseStatus: $"HTTP_{(int)response.StatusCode}",
                            scoredCandidates,
                            selectionReason: repeatedLast
                                ? $"Promoted top candidate '{topCandidate.TacticName}' over repeated LLM tactic '{lastUsed}'"
                                : $"LLM selected '{parsed.TacticName}' aligned with contextual evaluation");

                        parsed.RawJson = SerializeCanonicalPlanJson(parsed, team, roundNumber);
                        parsed.IsCustomPlayerCall = !string.IsNullOrEmpty(customPlayerCall);
                        RecordTeamTacticUsed(team, parsed.TacticName);

                        lock (_historyLock)
                        {
                            _decisionCache[$"{teamTag}_{buyState}"] = parsed;
                        }

                        return parsed;
                    }
                    else
                    {
                        callTelemetry.ParseResult = "DESERIALIZE_RETURNED_NULL";
                        callTelemetry.FallbackReason = "INVALID_TACTICAL_PLAN_JSON";
                    }
                }
                else
                {
                    callTelemetry.ParseResult = "MISSING_RESPONSE_PROPERTY";
                    callTelemetry.FallbackReason = "MISSING_RESPONSE_JSON_FIELD";
                }
            }
            else
            {
                callTelemetry.ParseResult = $"HTTP_STATUS_{(int)response.StatusCode}";
                callTelemetry.FallbackReason = $"OLLAMA_HTTP_ERROR_{(int)response.StatusCode}";
            }

            TelemetryLogger?.LogEvent("IGL_CALL_TELEMETRY", callTelemetry.ToLogString());
            return GenerateDeterministicFallbackPlan(
                team,
                buyState,
                mapProfileManager,
                callTelemetry.FallbackReason,
                roundNumber,
                internalRoundId,
                requestedAtTick,
                completedTick,
                sw.Elapsed.TotalMilliseconds,
                scoredCandidates,
                decisionId);
        }
        catch (OperationCanceledException ex)
        {
            sw.Stop();
            callTelemetry.TotalMs = (float)sw.Elapsed.TotalMilliseconds;
            callTelemetry.Cancelled = true;
            callTelemetry.CancellationSource = cancellationToken.IsCancellationRequested ? "TOKEN_CANCELLED" : "EXTERNAL_CANCEL";
            callTelemetry.TimeoutSource = cancellationToken.IsCancellationRequested ? $"TIMEOUT_{Config.OllamaDecisionTimeoutMs}MS" : "NONE";
            callTelemetry.ExceptionType = ex.GetType().Name;
            callTelemetry.ExceptionMessage = SanitizeExceptionMessage(ex.Message);
            callTelemetry.FallbackReason = $"TIMEOUT_{sw.Elapsed.TotalMilliseconds:F0}MS";
            callTelemetry.ParseResult = "CANCELLED";

            TelemetryLogger?.LogEvent("IGL_CALL_TELEMETRY", callTelemetry.ToLogString());

            int completedTick = tickProvider?.Invoke() ?? requestedAtTick;
            TelemetryLogger?.LogEvent("IGL_TIMEOUT",
                $"[{teamTag}] Timeout/Cancelamento após {sw.Elapsed.TotalMilliseconds:F0}ms (DecisionId={decisionId}). Acionando DeterministicPolicy.");
            return GenerateDeterministicFallbackPlan(
                team,
                buyState,
                mapProfileManager,
                $"TIMEOUT_{sw.Elapsed.TotalMilliseconds:F0}MS",
                roundNumber,
                internalRoundId,
                requestedAtTick,
                completedTick,
                sw.Elapsed.TotalMilliseconds,
                scoredCandidates,
                decisionId);
        }
        catch (Exception ex)
        {
            sw.Stop();
            callTelemetry.TotalMs = (float)sw.Elapsed.TotalMilliseconds;
            callTelemetry.ExceptionType = ex.GetType().Name;
            callTelemetry.ExceptionMessage = SanitizeExceptionMessage(ex.Message);
            callTelemetry.FallbackReason = $"{ex.GetType().Name}: {callTelemetry.ExceptionMessage}";
            callTelemetry.ParseResult = "EXCEPTION";

            TelemetryLogger?.LogEvent("IGL_CALL_TELEMETRY", callTelemetry.ToLogString());

            int completedTick = tickProvider?.Invoke() ?? requestedAtTick;
            Console.WriteLine($"[OllamaIglService] Fallback acionado ({team}): {ex.GetType().Name} - {ex.Message}");
            TelemetryLogger?.LogEvent("IGL_FALLBACK", $"Fallback acionado para {team}: {ex.GetType().Name} - {ex.Message}");
            return GenerateDeterministicFallbackPlan(
                team,
                buyState,
                mapProfileManager,
                $"{ex.GetType().Name}: {ex.Message}",
                roundNumber,
                internalRoundId,
                requestedAtTick,
                completedTick,
                sw.Elapsed.TotalMilliseconds,
                scoredCandidates,
                decisionId);
        }
    }

    private static string SanitizeExceptionMessage(string? msg)
    {
        if (string.IsNullOrWhiteSpace(msg)) return "NONE";
        return msg.Replace("\r", " ").Replace("\n", " ").Replace("|", "/").Trim();
    }

    private static string CleanMarkdownJson(string input)
    {
        string jsonString = input.Trim();
        if (jsonString.StartsWith("```json", StringComparison.OrdinalIgnoreCase))
            jsonString = jsonString[7..];
        else if (jsonString.StartsWith("```"))
            jsonString = jsonString[3..];

        if (jsonString.EndsWith("```"))
            jsonString = jsonString[..^3];

        return jsonString.Trim();
    }

    private void PopulateAuditMetadata(
        TacticalPlan plan,
        string decisionId,
        int internalRoundId,
        CsTeam team,
        int requestedTick,
        int completedTick,
        double latencyMs,
        TacticalDecisionSource source,
        bool fallbackUsed,
        string fallbackReason,
        string parseStatus,
        string modelResponseStatus,
        List<CandidateTacticScore> candidates,
        string selectionReason)
    {
        plan.DecisionId = decisionId;
        plan.RoundId = internalRoundId;
        plan.Team = team;
        plan.TeamSide = team;
        plan.RequestedAtTick = requestedTick;
        plan.CompletedAtTick = completedTick;
        plan.LatencyMs = Math.Round(latencyMs, 2);
        plan.Source = source;
        plan.TacticSource = source.ToString();
        plan.FallbackUsed = fallbackUsed;
        plan.FallbackReason = fallbackReason;
        plan.ParseStatus = parseStatus;
        plan.ModelResponseStatus = modelResponseStatus;
        plan.SelectedTactic = plan.TacticName;
        plan.InitialTactic = plan.TacticName;
        plan.CurrentTactic = plan.TacticName;
        plan.TacticRevision = 1;
        plan.CandidateTactics = candidates.Select(c => c.TacticName).ToList();
        plan.SelectionScores = candidates.ToDictionary(c => c.TacticName, c => Math.Round((double)c.FinalScore, 1));
        plan.SelectionReason = selectionReason;
        plan.RepetitionPenaltyApplied = candidates.Any(c => c.RepetitionPenalty > 0.0f);
    }

    public TacticalPlan BuildPlanFromCandidate(CandidateTacticScore candidate, CsTeam team, MapProfileManager? mapProfileManager)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        var plan = new TacticalPlan
        {
            TacticName = candidate.TacticName,
            CurrentTactic = candidate.TacticName,
            InitialTactic = candidate.TacticName,
            TacticSummary = candidate.Summary,
            RoundTempo = candidate.RecommendedTempo,
            StagingDurationSeconds = candidate.RecommendedStagingSeconds
        };

        string nameLower = candidate.TacticName.ToLowerInvariant();

        if (isCt)
        {
            if (nameLower.Contains("meio"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Mid Window",
                    RoleAction = "Hold aggressive sniper line on Top Mid",
                    StagingSpotId = "ct_mid_window_deep_awp",
                    ExecuteSpotId = "ct_mid_window_crouch",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Connector",
                    RoleAction = "Aggressive mid/connector contest",
                    StagingSpotId = "ct_mid_connector_headshot",
                    ExecuteSpotId = "ct_a_stairs_cross",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite A",
                    RoleAction = "Hold A ramp and support connector",
                    StagingSpotId = "ct_a_stairs_cross",
                    ExecuteSpotId = "ct_a_ticket_box_awp",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Anchor B site and catwalk info",
                    StagingSpotId = "ct_b_van_peek",
                    ExecuteSpotId = "ct_b_site_default_crouch",
                    Stance = EngagementStance.JIGGLE_INFO
                };
            }
            else if (nameLower.Contains("stack a"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite A",
                    RoleAction = "Hold A ramp from Ticket/CT",
                    StagingSpotId = "ct_a_ticket_box_awp",
                    ExecuteSpotId = "ct_a_ticket_box_awp",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite A",
                    RoleAction = "Close Palace & Ramp crossfire",
                    StagingSpotId = "ct_a_palace_close_poke",
                    ExecuteSpotId = "ct_a_firebox_oneanddone",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Connector",
                    RoleAction = "Hold Stairs/Jungle crossfire",
                    StagingSpotId = "ct_a_stairs_cross",
                    ExecuteSpotId = "ct_jungle_safe",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Passive B info for retake",
                    StagingSpotId = "ct_b_bench_deep",
                    ExecuteSpotId = "ct_b_site_default_crouch",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
            }
            else if (nameLower.Contains("anti-split b"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Mid Window",
                    RoleAction = "Watch Top Mid to Catwalk cross",
                    StagingSpotId = "ct_mid_window_deep_awp",
                    ExecuteSpotId = "ct_mid_window_crouch",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Contest Apartments from Van",
                    StagingSpotId = "ct_b_van_peek",
                    ExecuteSpotId = "ct_b_site_default_crouch",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Hold Short/Catwalk and Market crossfire",
                    StagingSpotId = "ct_b_site_default_crouch",
                    ExecuteSpotId = "ct_b_bench_deep",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite A",
                    RoleAction = "Solo A anchor at Ticket/Stairs",
                    StagingSpotId = "ct_a_stairs_cross",
                    ExecuteSpotId = "ct_a_ticket_box_awp",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
            }
            else
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Mid Window",
                    RoleAction = "Hold long angle on Mid",
                    StagingSpotId = "ct_mid_window_deep_awp",
                    ExecuteSpotId = "ct_mid_window_crouch",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite A",
                    RoleAction = "Hold Palace and Ramp",
                    StagingSpotId = "ct_a_palace_close_poke",
                    ExecuteSpotId = "ct_a_stairs_cross",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Connector",
                    RoleAction = "Connector pivot between Mid and A",
                    StagingSpotId = "ct_mid_connector_headshot",
                    ExecuteSpotId = "ct_a_stairs_cross",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Anchor B site",
                    StagingSpotId = "ct_b_van_peek",
                    ExecuteSpotId = "ct_b_site_default_crouch",
                    Stance = EngagementStance.JIGGLE_INFO
                };
            }
        }
        else // TR
        {
            if (nameLower.Contains("fake a"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Ramp A",
                    RoleAction = "Fake pressure on A Ramp with sniper line",
                    StagingSpotId = "tr_staging_a_ramp",
                    ExecuteSpotId = "tr_exec_a_triple_clear",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Palace",
                    RoleAction = "Fake Palace presence with sounds/flashes",
                    StagingSpotId = "tr_staging_palace_room",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Fast push Apartments B into site during A fake",
                    StagingSpotId = "tr_staging_b_apartments_kitchen",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Advance Apartments B with C4 and plant at B Site",
                    StagingSpotId = "tr_staging_b_apartments_kitchen",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.JIGGLE_INFO
                };
            }
            else if (nameLower.Contains("fake b"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Apartments B",
                    RoleAction = "Fake pressure on Apartments B",
                    StagingSpotId = "tr_staging_b_apartments_house",
                    ExecuteSpotId = "tr_exec_b_van_clear",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Underpass",
                    RoleAction = "Fake Underpass noise and push towards Catwalk",
                    StagingSpotId = "tr_staging_underpass_top",
                    ExecuteSpotId = "tr_exec_b_market_push",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Palace",
                    RoleAction = "Infiltrate Palace into A Site during B fake",
                    StagingSpotId = "tr_staging_palace_room",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Ramp A",
                    RoleAction = "Advance Ramp A with C4 and plant at A Default",
                    StagingSpotId = "tr_staging_a_ramp",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.JIGGLE_INFO
                };
            }
            else if (nameLower.Contains("execução b"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Apartments B",
                    RoleAction = "Cover B apps long angle",
                    StagingSpotId = "tr_staging_b_apps_kitchen",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Entry B Van and Default",
                    StagingSpotId = "tr_staging_b_apps_balcony",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Trade entry and plant C4 on B",
                    StagingSpotId = "tr_staging_b_apps_kitchen",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Underpass",
                    RoleAction = "Lurk Underpass/Short B",
                    StagingSpotId = "tr_staging_underpass_top",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
            }
            else if (nameLower.Contains("split b"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Top Mid",
                    RoleAction = "Pin Mid Window sniper",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Push Short/Catwalk into B",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Bombsite B",
                    RoleAction = "Advance Apartments B with C4",
                    StagingSpotId = "tr_staging_b_apps_kitchen",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Underpass",
                    RoleAction = "Clear Underpass to Short B",
                    StagingSpotId = "tr_staging_underpass_top",
                    ExecuteSpotId = "tr_exec_b_site_plant",
                    Stance = EngagementStance.JIGGLE_INFO
                };
            }
            else if (nameLower.Contains("split a"))
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Top Mid",
                    RoleAction = "Hold Top Mid and cross to Connector",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_exec_mid_connector_push",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Palace",
                    RoleAction = "Entry Bombsite A from Palace",
                    StagingSpotId = "tr_staging_palace_room",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Ramp A",
                    RoleAction = "Entry Ramp A with C4 for plant",
                    StagingSpotId = "tr_staging_a_ramp",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Connector",
                    RoleAction = "Push Underpass to Connector",
                    StagingSpotId = "tr_staging_underpass_top",
                    ExecuteSpotId = "tr_exec_mid_connector_push",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
            }
            else // Execução A
            {
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
                {
                    TargetArea = "Ramp A",
                    RoleAction = "Hold Ticket/CT angle from Ramp",
                    StagingSpotId = "tr_staging_a_ramp",
                    ExecuteSpotId = "tr_exec_a_triple_clear",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
                {
                    TargetArea = "Palace",
                    RoleAction = "Entry A Default from Palace",
                    StagingSpotId = "tr_staging_palace_room",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.AGGRESSIVE_POKE
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
                {
                    TargetArea = "Ramp A",
                    RoleAction = "Advance Ramp A and plant C4 at Default",
                    StagingSpotId = "tr_staging_a_ramp",
                    ExecuteSpotId = "tr_exec_a_site_default",
                    Stance = EngagementStance.JIGGLE_INFO
                };
                plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
                {
                    TargetArea = "Top Mid",
                    RoleAction = "Lurk Mid/Connector to cut rotations",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_exec_a_stairs_clear",
                    Stance = EngagementStance.PASSIVE_HOLD
                };
            }
        }

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }

    private void EnsureValidBotOrders(TacticalPlan plan, CsTeam team, MapProfileManager? mapProfileManager)
    {
        string expectedSide = team == CsTeam.CounterTerrorist ? "CT" : "TR";
        bool isFakeA = plan.CurrentTactic.Contains("Fake A", StringComparison.OrdinalIgnoreCase);
        bool isFakeB = plan.CurrentTactic.Contains("Fake B", StringComparison.OrdinalIgnoreCase);
        string tacticBombsite;
        if (isFakeA) tacticBombsite = "B";
        else if (isFakeB) tacticBombsite = "A";
        else tacticBombsite = plan.CurrentTactic.Contains(" B", StringComparison.OrdinalIgnoreCase) ? "B"
            : (plan.CurrentTactic.Contains(" A", StringComparison.OrdinalIgnoreCase) ? "A" : "Mid");
        bool isFake = isFakeA || isFakeB || plan.CurrentTactic.Contains("FAKE", StringComparison.OrdinalIgnoreCase);

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

            bool isC4 = (team == CsTeam.Terrorist && role == BotRole.Rotator);
            PresetSpatialValidator.ValidateAndApplyFallback(
                order,
                role,
                plan.CurrentTactic,
                tacticBombsite,
                team,
                isC4,
                allowCrossSiteLurk: role == BotRole.Anchor,
                isFakeTactic: isFake,
                mapProfileManager);

            if (string.IsNullOrEmpty(order.FallbackSpotId))
            {
                order.FallbackSpotId = expectedSide == "CT" ? "ct_spawn_safe" : "tr_spawn_safe";
            }
        }
    }

    public static (int ValidCount, int InvalidCount, List<string> MissingSpots) ValidateTacticalPlanPresets(
        TacticalPlan plan,
        MapProfileManager? mapProfileManager)
    {
        int valid = 0;
        int invalid = 0;
        var missing = new List<string>();

        foreach (var kvp in plan.BotOrders)
        {
            var order = kvp.Value;
            var stSpot = mapProfileManager?.GetSpotById(order.StagingSpotId);
            var exSpot = mapProfileManager?.GetSpotById(order.ExecuteSpotId);

            if (mapProfileManager != null)
            {
                if (stSpot == null) missing.Add(order.StagingSpotId);
                if (exSpot == null) missing.Add(order.ExecuteSpotId);
            }

            bool targetIsB = order.TargetArea.Contains("B", StringComparison.OrdinalIgnoreCase);
            bool spotIsA = stSpot != null
                ? (stSpot.Sector.Contains("A", StringComparison.OrdinalIgnoreCase) || stSpot.Id.Contains("_a_"))
                : order.StagingSpotId.Contains("_a_");

            bool isConsistent = !(targetIsB && spotIsA && !order.StagingSpotId.Contains("mid") && !order.StagingSpotId.Contains("underpass"));
            if (isConsistent)
            {
                valid++;
            }
            else
            {
                invalid++;
                if (!missing.Contains(order.StagingSpotId)) missing.Add(order.StagingSpotId);
            }
        }

        return (valid, invalid, missing);
    }

    public TacticalPlan GenerateDeterministicFallbackPlan(
        CsTeam team,
        BuyState buyState,
        MapProfileManager? mapProfileManager,
        string? reason = null,
        int roundNumber = 1,
        int internalRoundId = 0,
        int requestedAtTick = 0,
        int completedAtTick = 0,
        double latencyMs = 0.0,
        List<CandidateTacticScore>? preScoredCandidates = null,
        string? existingDecisionId = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        string teamTag = isCt ? "CT" : "TR";
        string reasonClean = string.IsNullOrEmpty(reason) ? "DeterministicPolicy" : reason.Replace("\"", "'").Replace("\r", " ").Replace("\n", " ");

        var candidates = preScoredCandidates ?? EvaluateCandidateTactics(team, buyState, roundNumber, 3500);
        var bestCandidate = candidates.First();

        var plan = BuildPlanFromCandidate(bestCandidate, team, mapProfileManager);
        string decisionId = existingDecisionId ?? $"DEC-R{(internalRoundId > 0 ? internalRoundId : roundNumber):D2}-{teamTag}-FALLBACK";

        PopulateAuditMetadata(
            plan,
            decisionId,
            internalRoundId > 0 ? internalRoundId : roundNumber,
            team,
            requestedAtTick,
            completedAtTick,
            latencyMs,
            TacticalDecisionSource.FALLBACK_PRESET,
            fallbackUsed: true,
            fallbackReason: reasonClean,
            parseStatus: "DETERMINISTIC_FALLBACK",
            modelResponseStatus: reasonClean,
            candidates,
            selectionReason: $"Highest contextual score ({bestCandidate.FinalScore:F1}) with repetition penalty ({bestCandidate.RepetitionPenalty:F1}): {bestCandidate.Rationale}");

        plan.RawJson = SerializeCanonicalPlanJson(plan, team, roundNumber);
        RecordTeamTacticUsed(team, plan.TacticName);

        return plan;
    }

    private static string SerializeCanonicalPlanJson(TacticalPlan plan, CsTeam team, int roundNumber)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        return JsonSerializer.Serialize(new
        {
            decisionId = plan.DecisionId,
            side = isCt ? "CT" : "TR",
            round = roundNumber,
            source = plan.Source.ToString(),
            fallbackUsed = plan.FallbackUsed,
            fallbackReason = plan.FallbackReason,
            latencyMs = plan.LatencyMs,
            tacticName = plan.TacticName,
            initialTactic = plan.InitialTactic,
            currentTactic = plan.CurrentTactic,
            tacticRevision = plan.TacticRevision,
            summary = plan.TacticSummary,
            tempo = plan.RoundTempo.ToString(),
            stagingDuration = plan.StagingDurationSeconds,
            candidateTactics = plan.CandidateTactics,
            selectionScores = plan.SelectionScores,
            selectionReason = plan.SelectionReason,
            botOrders = plan.BotOrders
        }, new JsonSerializerOptions { WriteIndented = false });
    }
}
