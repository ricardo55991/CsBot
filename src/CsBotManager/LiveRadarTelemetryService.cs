using System.Text.Json;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class RadarPlayerDto
{
    [JsonPropertyName("slot")] public int Slot { get; set; }
    [JsonPropertyName("name")] public string Name { get; set; } = string.Empty;
    [JsonPropertyName("team")] public string Team { get; set; } = string.Empty;
    [JsonPropertyName("is_human")] public bool IsHuman { get; set; }
    [JsonPropertyName("is_bot")] public bool IsBot { get; set; }
    [JsonPropertyName("is_alive")] public bool IsAlive { get; set; }
    [JsonPropertyName("hp")] public int Hp { get; set; }
    [JsonPropertyName("armor")] public int Armor { get; set; }
    [JsonPropertyName("has_helmet")] public bool HasHelmet { get; set; }
    [JsonPropertyName("money")] public int Money { get; set; }
    [JsonPropertyName("weapon")] public string Weapon { get; set; } = string.Empty;
    [JsonPropertyName("x")] public float X { get; set; }
    [JsonPropertyName("y")] public float Y { get; set; }
    [JsonPropertyName("z")] public float Z { get; set; }
    [JsonPropertyName("yaw")] public float Yaw { get; set; }
    [JsonPropertyName("role")] public string Role { get; set; } = string.Empty;
    [JsonPropertyName("spot")] public string Spot { get; set; } = string.Empty;
    [JsonPropertyName("stance")] public string Stance { get; set; } = string.Empty;
    [JsonPropertyName("action")] public string Action { get; set; } = string.Empty;
    [JsonPropertyName("is_spotted")] public bool IsSpotted { get; set; }
}

public class RadarC4Dto
{
    [JsonPropertyName("is_planted")] public bool IsPlanted { get; set; }
    [JsonPropertyName("is_dropped")] public bool IsDropped { get; set; }
    [JsonPropertyName("is_defusing")] public bool IsDefusing { get; set; }
    [JsonPropertyName("is_spotted")] public bool IsSpotted { get; set; }
    [JsonPropertyName("site")] public string Site { get; set; } = string.Empty;
    [JsonPropertyName("time_to_explode")] public float TimeToExplode { get; set; }
    [JsonPropertyName("defuse_countdown")] public float DefuseCountdown { get; set; }
    [JsonPropertyName("carrier_name")] public string CarrierName { get; set; } = string.Empty;
    [JsonPropertyName("x")] public float X { get; set; }
    [JsonPropertyName("y")] public float Y { get; set; }
    [JsonPropertyName("z")] public float Z { get; set; }
}

public class RadarStateDto
{
    [JsonPropertyName("map")] public string Map { get; set; } = "de_mirage";
    [JsonPropertyName("ct_score")] public int CtScore { get; set; }
    [JsonPropertyName("tr_score")] public int TrScore { get; set; }
    [JsonPropertyName("round")] public int Round { get; set; }
    [JsonPropertyName("phase")] public string Phase { get; set; } = "FREEZETIME";
    [JsonPropertyName("is_warmup")] public bool IsWarmup { get; set; }
    [JsonPropertyName("is_freezetime")] public bool IsFreezeTime { get; set; }
    [JsonPropertyName("is_paused")] public bool IsPaused { get; set; }
    [JsonPropertyName("staging_time_remaining")] public float StagingTimeRemaining { get; set; }
    [JsonPropertyName("buy_state")] public string BuyState { get; set; } = "FULL_BUY";
    [JsonPropertyName("team_money")] public int TeamMoney { get; set; }
    [JsonPropertyName("tactic_name")] public string TacticName { get; set; } = string.Empty;
    [JsonPropertyName("tactic_summary")] public string TacticSummary { get; set; } = string.Empty;
    [JsonPropertyName("tempo")] public string Tempo { get; set; } = string.Empty;
    [JsonPropertyName("tier")] public string Tier { get; set; } = string.Empty;
    [JsonPropertyName("alerts")] public List<string> Alerts { get; set; } = new();
    [JsonPropertyName("last_voice_command")] public string LastVoiceCommand { get; set; } = string.Empty;
    [JsonPropertyName("last_voice_action")] public string LastVoiceAction { get; set; } = string.Empty;
    [JsonPropertyName("c4")] public RadarC4Dto C4 { get; set; } = new();
    [JsonPropertyName("players")] public List<RadarPlayerDto> Players { get; set; } = new();
}

public class LiveRadarTelemetryService
{
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly EconomyManager _economyManager;
    private readonly PacingAndFallbackController _pacingController;
    private readonly Func<TacticalPlan> _getCurrentPlan;
    private readonly VoiceCommandBridge? _voiceBridge;

    private byte[] _cachedJsonBytes = System.Text.Encoding.UTF8.GetBytes("{\"status\":\"waiting_data\"}");
    private readonly object _syncRoot = new();

    public LiveRadarTelemetryService(
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        EconomyManager economyManager,
        PacingAndFallbackController pacingController,
        Func<TacticalPlan> getCurrentPlan,
        VoiceCommandBridge? voiceBridge)
    {
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _economyManager = economyManager;
        _pacingController = pacingController;
        _getCurrentPlan = getCurrentPlan;
        _voiceBridge = voiceBridge;
    }

    public byte[] GetLatestStateBytes()
    {
        lock (_syncRoot)
        {
            return _cachedJsonBytes;
        }
    }

    public void UpdateTick(
        float currentTime,
        int tickCount,
        int currentRound,
        int ctScore,
        int trScore,
        bool isWarmup,
        bool isFreezeTime,
        bool isPaused)
    {
        // Atualiza a cada 3 ticks (aprox. 21Hz a 64Hz) para máxima eficiência de CPU (< 0.1ms)
        if (tickCount % 3 != 0) return;

        try
        {
            var plan = _getCurrentPlan();
            var allPlayers = Utilities.GetPlayers().Where(p => p != null && p.IsValid && !p.IsHLTV).ToList();
            var human = allPlayers.FirstOrDefault(p => !p.IsBot);
            var humanTeam = human?.Team ?? CsTeam.CounterTerrorist;

            var dto = new RadarStateDto
            {
                Map = Server.MapName ?? "de_mirage",
                CtScore = ctScore,
                TrScore = trScore,
                Round = currentRound,
                Phase = plan.CurrentPhase.ToString(),
                IsWarmup = isWarmup,
                IsFreezeTime = isFreezeTime,
                IsPaused = isPaused,
                StagingTimeRemaining = MathF.Max(0.0f, _pacingController.StagingTimeRemaining),
                BuyState = _economyManager.CurrentBuyState.ToString(),
                TacticName = plan.TacticName ?? string.Empty,
                TacticSummary = plan.TacticSummary ?? string.Empty,
                Tempo = plan.RoundTempo.ToString(),
                Tier = plan.PlayTier.ToString(),
                LastVoiceCommand = _voiceBridge?.LastVoiceCommand ?? string.Empty,
                LastVoiceAction = _voiceBridge?.LastVoiceAction ?? string.Empty
            };

            // 1. Alertas Táticos
            if (plan.IsTacticalSaveActive) dto.Alerts.Add("SAVE TÁTICO");
            if (plan.IsHeroicAttempt) dto.Alerts.Add("CLUTCH HEROICO");
            if (plan.IsFlankCoverActive) dto.Alerts.Add("ANTI-RUSH ATIVO");
            if (plan.CurrentAlertLevel == AlertLevel.Level1_PressureNoBomb) dto.Alerts.Add("ALERTA: PRESSÃO NO BOMB");
            if (plan.CurrentAlertLevel == AlertLevel.Level2_BombConfirmed) dto.Alerts.Add("ALERTA: C4 CONFIRMADA");
            if (plan.CtDuoPlay != CtDuoPlayType.None) dto.Alerts.Add($"DUO PLAY: {plan.CtDuoPlay}");

            // 2. Estado da Bomba (C4) - Regras Competitivas Oficiais CS2
            var plantedC4 = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4").FirstOrDefault(c => c.IsValid && c.AbsOrigin != null);
            if (plantedC4 != null)
            {
                dto.C4.IsPlanted = true;
                dto.C4.IsDropped = false;
                dto.C4.IsDefusing = plantedC4.BeingDefused;
                dto.C4.TimeToExplode = MathF.Max(0.0f, plantedC4.C4Blow - currentTime);
                dto.C4.DefuseCountdown = MathF.Max(0.0f, plantedC4.DefuseCountDown - currentTime);
                dto.C4.X = plantedC4.AbsOrigin!.X;
                dto.C4.Y = plantedC4.AbsOrigin!.Y;
                dto.C4.Z = plantedC4.AbsOrigin!.Z;

                string realSite = plantedC4.BombSite == 0 ? "A" : "B";

                // Se o time do jogador for TR, a localização da C4 armada é sempre conhecida.
                // Se for CT, só é revelada no radar se alguém a avistar ou confirmar (regra competitiva oficial).
                bool isSpotted = false;
                if (humanTeam == CsTeam.Terrorist)
                {
                    isSpotted = true;
                }
                else
                {
                    if (plantedC4.BeingDefused || plan.CurrentAlertLevel == AlertLevel.Level2_BombConfirmed)
                    {
                        isSpotted = true;
                    }
                    else
                    {
                        try
                        {
                            if (plantedC4.EntitySpottedState != null && plantedC4.EntitySpottedState.Spotted)
                            {
                                isSpotted = true;
                            }
                        }
                        catch { }

                        if (!isSpotted)
                        {
                            foreach (var p in allPlayers)
                            {
                                if (p.Team == CsTeam.CounterTerrorist && p.PawnIsAlive && p.PlayerPawn.Value?.AbsOrigin != null)
                                {
                                    var pOrigin = p.PlayerPawn.Value.AbsOrigin;
                                    float dx = pOrigin.X - plantedC4.AbsOrigin!.X;
                                    float dy = pOrigin.Y - plantedC4.AbsOrigin!.Y;
                                    float dz = pOrigin.Z - plantedC4.AbsOrigin!.Z;
                                    if ((dx * dx + dy * dy + dz * dz) <= 900f * 900f)
                                    {
                                        isSpotted = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }

                dto.C4.IsSpotted = isSpotted;
                dto.C4.Site = isSpotted ? realSite : "?";
            }
            else
            {
                var droppedC4 = Utilities.FindAllEntitiesByDesignerName<CC4>("weapon_c4").FirstOrDefault(c => c.IsValid && c.AbsOrigin != null);
                if (droppedC4 != null)
                {
                    dto.C4.IsPlanted = false;
                    dto.C4.IsDropped = true;
                    dto.C4.X = droppedC4.AbsOrigin!.X;
                    dto.C4.Y = droppedC4.AbsOrigin!.Y;
                    dto.C4.Z = droppedC4.AbsOrigin!.Z;

                    bool isSpotted = false;
                    if (humanTeam == CsTeam.Terrorist)
                    {
                        isSpotted = true;
                    }
                    else
                    {
                        try
                        {
                            if (droppedC4.EntitySpottedState != null && droppedC4.EntitySpottedState.Spotted)
                            {
                                isSpotted = true;
                            }
                        }
                        catch { }

                        if (!isSpotted)
                        {
                            foreach (var p in allPlayers)
                            {
                                if (p.Team == CsTeam.CounterTerrorist && p.PawnIsAlive && p.PlayerPawn.Value?.AbsOrigin != null)
                                {
                                    var pOrigin = p.PlayerPawn.Value.AbsOrigin;
                                    float dx = pOrigin.X - droppedC4.AbsOrigin!.X;
                                    float dy = pOrigin.Y - droppedC4.AbsOrigin!.Y;
                                    if ((dx * dx + dy * dy) <= 650f * 650f)
                                    {
                                        isSpotted = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    dto.C4.IsSpotted = isSpotted;
                }
                else
                {
                    dto.C4.IsPlanted = false;
                    dto.C4.IsDropped = false;
                    dto.C4.IsSpotted = false;
                }
            }

            // 3. Mapeamento de Jogadores
            int teamCashSum = 0;
            foreach (var p in allPlayers)
            {
                var pawn = p.PlayerPawn.Value;
                bool isAlive = p.PawnIsAlive && pawn != null;
                string teamStr = p.Team == CsTeam.CounterTerrorist ? "CT" : (p.Team == CsTeam.Terrorist ? "TR" : "SPEC");

                int money = p.InGameMoneyServices?.Account ?? 0;
                if (p.Team == humanTeam)
                {
                    teamCashSum += money;
                }

                // Identifica se o jogador é o portador da C4
                if (!dto.C4.IsPlanted && !dto.C4.IsDropped && p.Team == CsTeam.Terrorist && isAlive)
                {
                    var weapons = pawn?.WeaponServices?.MyWeapons;
                    if (weapons != null)
                    {
                        foreach (var w in weapons)
                        {
                            if (w?.Value?.DesignerName == "weapon_c4")
                            {
                                dto.C4.CarrierName = p.PlayerName;
                                break;
                            }
                        }
                    }
                }

                string weaponName = pawn?.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Replace("weapon_", "") ?? "none";
                float posX = pawn?.AbsOrigin?.X ?? 0f;
                float posY = pawn?.AbsOrigin?.Y ?? 0f;
                float posZ = pawn?.AbsOrigin?.Z ?? 0f;
                float yaw = pawn?.EyeAngles?.Y ?? 0f;

                string roleStr = "";
                string spotStr = "";
                string stanceStr = "";
                string actionStr = "";

                if (p.IsBot)
                {
                    var role = _roleManager.GetBotRole(p);
                    roleStr = role?.ToString() ?? "Bot";

                    if (role != null)
                    {
                        string orderKey = RoleManager.GetOrderKey(role.Value);
                        if (plan.BotOrders.TryGetValue(orderKey, out var order))
                        {
                            string activeSpotId = (plan.CurrentPhase == RoundPhase.Executing)
                                ? order.ExecuteSpotId
                                : order.StagingSpotId;

                            var spot = _mapProfileManager.GetSpotById(activeSpotId);
                            spotStr = spot?.Name ?? order.TargetArea;

                            stanceStr = order.IsFallingBack ? "Recuando" : order.HoldSiteLocked ? "Travado B" : order.Stance switch
                            {
                                EngagementStance.PASSIVE_HOLD => "Passivo",
                                EngagementStance.JIGGLE_INFO => "Jiggle-Peek",
                                EngagementStance.ONE_AND_DONE => "One&Done",
                                EngagementStance.AGGRESSIVE_POKE => "Poke",
                                _ => "Hold"
                            };

                            actionStr = order.HoldSiteLocked ? "Travado B" : (order.IsFallingBack ? "Recuando" : "Cobrir Ângulo");
                        }
                    }
                }
                else
                {
                    roleStr = "Humano (Você)";
                    spotStr = MirageSectorClassifier.ClassifyPlayer(p).SectorName;
                    stanceStr = "Livre";
                    actionStr = "Comandante";
                }

                bool isSpotted = false;
                if (pawn != null)
                {
                    try
                    {
                        isSpotted = pawn.EntitySpottedState != null && pawn.EntitySpottedState.Spotted;
                    }
                    catch { }
                }

                dto.Players.Add(new RadarPlayerDto
                {
                    Slot = p.Slot,
                    Name = p.PlayerName,
                    Team = teamStr,
                    IsHuman = !p.IsBot,
                    IsBot = p.IsBot,
                    IsAlive = isAlive,
                    Hp = pawn?.Health ?? 0,
                    Armor = pawn?.ArmorValue ?? 0,
                    HasHelmet = (pawn?.ItemServices as CCSPlayer_ItemServices)?.HasHelmet ?? false,
                    Money = money,
                    Weapon = weaponName,
                    X = posX,
                    Y = posY,
                    Z = posZ,
                    Yaw = yaw,
                    Role = roleStr,
                    Spot = spotStr,
                    Stance = stanceStr,
                    Action = actionStr,
                    IsSpotted = isSpotted
                });
            }

            dto.TeamMoney = teamCashSum;

            byte[] jsonBytes = JsonSerializer.SerializeToUtf8Bytes(dto);
            lock (_syncRoot)
            {
                _cachedJsonBytes = jsonBytes;
            }
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[LiveRadarTelemetryService] Erro ao serializar estado: {ex.Message}");
        }
    }
}
