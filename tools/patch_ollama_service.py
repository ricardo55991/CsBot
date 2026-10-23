with open(r'src/CsBotManager/OllamaIglService.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add TelemetryLogger and JsonOptions
target_class_start = """public class OllamaIglService
{
    private readonly HttpClient _httpClient;"""
target_class_start_crlf = target_class_start.replace('\n', '\r\n')

replacement_class_start = """public class OllamaIglService
{
    private readonly HttpClient _httpClient;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        AllowTrailingCommas = true,
        ReadCommentHandling = JsonCommentHandling.Skip
    };"""
replacement_class_start_crlf = replacement_class_start.replace('\n', '\r\n')

if target_class_start_crlf in text:
    text = text.replace(target_class_start_crlf, replacement_class_start_crlf, 1)
elif target_class_start in text:
    text = text.replace(target_class_start, replacement_class_start, 1)
else:
    raise AssertionError('target_class_start not found')

# 2. Update num_predict from 220 to 450 and temperature 0.3
target_req = """                options = new
                {
                    temperature = 0.4,
                    num_predict = 220
                }"""
target_req_crlf = target_req.replace('\n', '\r\n')

replacement_req = """                options = new
                {
                    temperature = 0.3,
                    num_predict = 450
                }"""
replacement_req_crlf = replacement_req.replace('\n', '\r\n')

if target_req_crlf in text:
    text = text.replace(target_req_crlf, replacement_req_crlf, 1)
elif target_req in text:
    text = text.replace(target_req, replacement_req, 1)
else:
    raise AssertionError('target_req not found')

# 3. Use JsonOptions in JsonSerializer.Deserialize
target_deser = """var parsed = JsonSerializer.Deserialize<TacticalPlan>(jsonString);"""
replacement_deser = """var parsed = JsonSerializer.Deserialize<TacticalPlan>(jsonString, JsonOptions);"""
assert target_deser in text, 'target_deser not found'
text = text.replace(target_deser, replacement_deser, 1)

# 4. Update catch(Exception) to log error and pass reason
target_catch = """        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception)
        {
            // Fallback determinístico
        }

        return GenerateDeterministicFallbackPlan(team, buyState, mapProfileManager);"""
target_catch_crlf = target_catch.replace('\n', '\r\n')

replacement_catch = """        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[OllamaIglService] Fallback acionado ({team}): {ex.GetType().Name} - {ex.Message}");
            TelemetryLogger?.LogEvent("IGL_FALLBACK", $"Fallback acionado para {team}: {ex.GetType().Name} - {ex.Message}");
            return GenerateDeterministicFallbackPlan(team, buyState, mapProfileManager, ex.Message);
        }

        return GenerateDeterministicFallbackPlan(team, buyState, mapProfileManager, "Resposta nula ou invalida");"""
replacement_catch_crlf = replacement_catch.replace('\n', '\r\n')

if target_catch_crlf in text:
    text = text.replace(target_catch_crlf, replacement_catch_crlf, 1)
elif target_catch in text:
    text = text.replace(target_catch, replacement_catch, 1)
else:
    raise AssertionError('target_catch not found')

# 5. Update GenerateDeterministicFallbackPlan signature and body
target_gen = """    private TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        var plan = new TacticalPlan
        {
            TacticName = isCt ? "Defesa Padrão 2-1-2" : (buyState == BuyState.FORCE_BUY ? "Rush B com Smoke Janela" : "Execução A com Domínio Palácio"),
            TacticSummary = isCt ? "Marcação de posições 2 A, 1 Meio e 2 B com paciência e crossfire" : (buyState == BuyState.FORCE_BUY ? "Entrada rápida na B explorando o apartamento" : "Staging controlado no palácio e rampa A com utilitárias"),
            RoundTempo = (isCt || buyState != BuyState.FORCE_BUY) ? RoundTempo.SLOW_DEFAULT : RoundTempo.FAST_CONTACT,
            StagingDurationSeconds = (isCt || buyState != BuyState.FORCE_BUY) ? 18.0f : 0.0f,
            RawJson = "{\\"fallback\\": true, \\"side\\": \\"" + (isCt ? "CT" : "TR") + "\\"}"
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }"""
target_gen_crlf = target_gen.replace('\n', '\r\n')

replacement_gen = """    public TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager, string? reason = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace("\"", "'").Replace("\r", " ").Replace("\n", " ");
        var plan = new TacticalPlan
        {
            TacticName = isCt ? "Defesa Padrão 2-1-2" : (buyState == BuyState.FORCE_BUY ? "Rush B com Smoke Janela" : "Execução A com Domínio Palácio"),
            TacticSummary = isCt ? "Marcação de posições 2 A, 1 Meio e 2 B com paciência e crossfire" : (buyState == BuyState.FORCE_BUY ? "Entrada rápida na B explorando o apartamento" : "Staging controlado no palácio e rampa A com utilitárias"),
            RoundTempo = (isCt || buyState != BuyState.FORCE_BUY) ? RoundTempo.SLOW_DEFAULT : RoundTempo.FAST_CONTACT,
            StagingDurationSeconds = (isCt || buyState != BuyState.FORCE_BUY) ? 18.0f : 0.0f,
            RawJson = "{\\"fallback\\": true, \\"side\\": \\"" + (isCt ? "CT" : "TR") + "\\", \\"reason\\": \\"" + reasonClean + "\\"}"
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }"""
replacement_gen_crlf = replacement_gen.replace('\n', '\r\n')

if target_gen_crlf in text:
    text = text.replace(target_gen_crlf, replacement_gen_crlf, 1)
elif target_gen in text:
    text = text.replace(target_gen, replacement_gen, 1)
else:
    raise AssertionError('target_gen not found')

with open(r'src/CsBotManager/OllamaIglService.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('OllamaIglService.cs patched successfully')
