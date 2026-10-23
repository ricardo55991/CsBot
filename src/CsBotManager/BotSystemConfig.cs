using System.Text;

namespace CsBotManager;

/// <summary>
/// Configuração centralizada e validada de todos os limiares físicos, táticos e econômicos do CsBot V4.
/// Nenhum valor crítico deve permanecer hardcoded fora desta estrutura.
/// </summary>
public sealed class BotSystemConfig
{
    public static BotSystemConfig Default { get; } = new();

    // 1. Detector de Stuck 2D & StandStill
    public float StuckTimeWindowSeconds { get; set; } = 3.5f;
    public float StuckMinDisplacement2D { get; set; } = 40.0f;
    public float StuckMinTargetProgress2D { get; set; } = 25.0f;
    public float WaypointBlacklistCooldownSeconds { get; set; } = 12.0f;
    public int MaxWaypointFailuresBeforeEscalate { get; set; } = 2;
    public float StandStillMaxAggressiveSeconds { get; set; } = 1.6f;
    public float StandStillMaxDefensiveSeconds { get; set; } = 5.0f;
    public float HotzoneMaxActiveSeconds { get; set; } = 2.0f;
    public float HotzoneCooldownSeconds { get; set; } = 8.0f;

    // 2. Arbitragem de Movimento
    public int ArbitrationHysteresisTicks { get; set; } = 8; // ~125ms em 64Hz
    public float MaxArtificialSpeed2D { get; set; } = 250.0f;

    // 3. Trade Spacing & Wide Swing
    public float TradeSpacingMinDist2D { get; set; } = 140.0f;
    public float TradeSpacingPairCooldownSeconds { get; set; } = 2.5f;
    public float TradeSpacingNavOffsetUnits { get; set; } = 145.0f;
    public float WideSwingMinDist2D { get; set; } = 250.0f;
    public float WideSwingMaxDist2D { get; set; } = 400.0f;

    // 4. Counter-Strafe
    public float CounterStrafeCooldownSeconds { get; set; } = 2.5f;
    public float CounterStrafeMaxAimErrorDegrees { get; set; } = 16.0f;
    public float CounterStrafeMinSpeed2D { get; set; } = 65.0f;
    public float CounterStrafeDurationSeconds { get; set; } = 0.14f;

    // 5. Pivô Tático & Detecção de Bombsite Limpo
    public float BombsiteClearMinDwellSeconds { get; set; } = 2.0f;
    public float BombsiteClearMinConfidence { get; set; } = 0.75f;
    public float BombsiteClearNoDamageWindowSeconds { get; set; } = 3.0f;
    public float BombsitePlantZoneRadius2D { get; set; } = 320.0f;

    // 6. Economia & Freeze Time
    public int PistolRoundFirstHalf { get; set; } = 1;
    public int PistolRoundSecondHalf { get; set; } = 13;
    public int CtFullBuyMinAvgCash { get; set; } = 4400;
    public int TrFullBuyMinAvgCash { get; set; } = 3900;
    public int CtFullBuyMinEquipmentValue { get; set; } = 18000;
    public int TrFullBuyMinEquipmentValue { get; set; } = 16000;
    public int FullBuyMinAvgEquipValue { get; set; } = 3600;
    public int HalfBuyMinAvgEquipValue { get; set; } = 2000;
    public int ForceBuyMinAvgSpend { get; set; } = 1100;
    public int LightBuyMinAvgSpend { get; set; } = 500;
    public float BuyStabilizationTimeoutSeconds { get; set; } = 13.5f;
    public int MaxStandardAwpPerTeam { get; set; } = 1;
    public int MaxDoubleAwpPerTeamCt { get; set; } = 2;

    // 7. IGL / Ollama
    public float OllamaTimeoutSeconds { get; set; } = 8.5f;
    public int OllamaDecisionTimeoutMs => (int)(OllamaTimeoutSeconds * 1000.0f);
    public float TacticRepetitionPenaltyScore { get; set; } = 32.0f;

    public bool Validate(out List<string> errors)
    {
        errors = new List<string>();
        if (StuckTimeWindowSeconds <= 0.5f) errors.Add("StuckTimeWindowSeconds must be > 0.5s.");
        if (StuckMinDisplacement2D <= 5.0f) errors.Add("StuckMinDisplacement2D must be > 5u.");
        if (TradeSpacingPairCooldownSeconds <= 0.1f) errors.Add("TradeSpacingPairCooldownSeconds must be > 0.1s.");
        if (WideSwingMinDist2D <= 0f || WideSwingMaxDist2D <= WideSwingMinDist2D) errors.Add("Invalid WideSwing distance window.");
        if (CounterStrafeCooldownSeconds <= 0.1f) errors.Add("CounterStrafeCooldownSeconds must be > 0.1s.");
        if (CounterStrafeMaxAimErrorDegrees <= 1.0f || CounterStrafeMaxAimErrorDegrees > 45.0f) errors.Add("CounterStrafeMaxAimErrorDegrees must be in (1, 45].");
        if (BombsiteClearMinDwellSeconds <= 0.2f) errors.Add("BombsiteClearMinDwellSeconds must be > 0.2s.");
        return errors.Count == 0;
    }

    public string FormatMarkdownSummary()
    {
        var sb = new StringBuilder();
        sb.AppendLine("### ⚙️ Parâmetros Configuráveis Ativos (BotSystemConfig V4)");
        sb.AppendLine($"- **Stuck 2D:** janela=`{StuckTimeWindowSeconds:F1}s`, deslocamento_min=`{StuckMinDisplacement2D:F0}u`, progresso_alvo_min=`{StuckMinTargetProgress2D:F0}u`, cooldown_waypoint=`{WaypointBlacklistCooldownSeconds:F1}s`");
        sb.AppendLine($"- **StandStill:** max_agressivo=`{StandStillMaxAggressiveSeconds:F2}s`, max_defensivo=`{StandStillMaxDefensiveSeconds:F2}s`, hotzone_max=`{HotzoneMaxActiveSeconds:F1}s` (cooldown=`{HotzoneCooldownSeconds:F1}s`)");
        sb.AppendLine($"- **Arbitragem de Movimento:** histerese=`{ArbitrationHysteresisTicks} ticks`, max_artificial_speed_2d=`{MaxArtificialSpeed2D:F0} u/s`");
        sb.AppendLine($"- **Trade Spacing & Wide Swing:** repulsao_min=`{TradeSpacingMinDist2D:F0}u`, pair_cooldown=`{TradeSpacingPairCooldownSeconds:F1}s`, nav_offset=`{TradeSpacingNavOffsetUnits:F0}u`, wide_swing_window=`[{WideSwingMinDist2D:F0}u, {WideSwingMaxDist2D:F0}u]` (2D)");
        sb.AppendLine($"- **Counter-Strafe:** cooldown=`{CounterStrafeCooldownSeconds:F1}s`, max_aim_error=`{CounterStrafeMaxAimErrorDegrees:F1}°`, min_speed_2d=`{CounterStrafeMinSpeed2D:F0} u/s`");
        sb.AppendLine($"- **Bombsite Clear & Pivôs:** permanencia_min=`{BombsiteClearMinDwellSeconds:F1}s`, confianca_min=`{BombsiteClearMinConfidence:F2}`, raio_plant_2d=`{BombsitePlantZoneRadius2D:F0}u`");
        sb.AppendLine($"- **Economia & IGL:** pistol_rounds=`[{PistolRoundFirstHalf}, {PistolRoundSecondHalf}]`, full_buy_equip=`${FullBuyMinAvgEquipValue}`, ollama_timeout=`{OllamaTimeoutSeconds:F1}s`, repetition_penalty=`{TacticRepetitionPenaltyScore:F2}`");
        return sb.ToString();
    }
}
