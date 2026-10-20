using System.Text.Json.Serialization;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum BuyState
{
    FULL_BUY,
    FORCE_BUY,
    HALF_BUY,
    FULL_ECO
}

public enum BotRole
{
    AWPer,
    EntryFragger,
    Rotator,
    Anchor
}

public enum RoundTempo
{
    SLOW_DEFAULT,
    POKE_AND_ROTATE,
    TIMED_EXECUTE,
    FAST_CONTACT
}

public enum EngagementStance
{
    PASSIVE_HOLD,
    JIGGLE_INFO,
    ONE_AND_DONE,
    AGGRESSIVE_POKE
}

public enum RoundPhase
{
    FreezeTime,
    Staging,
    Executing,
    PostPlant
}

public enum AlertLevel
{
    Level0_Default,
    Level1_PressureNoBomb,
    Level2_BombConfirmed
}

public enum CtDuoPlayType
{
    None,
    DominioCavernaRamp,
    DominioMeio,
    HumanPartner
}

public enum TrTacticType
{
    Default,
    SPLIT_FAKE
}

public enum MidRoundAction
{
    NORMAL,
    HIDE_COVER,
    JIGGLE_PEEK,
    ROTATE_SILENT,
    WATCH_FLANK,
    RUSH_TRADE
}

public enum PlayTier
{
    Tier1_Standard,    // 72%
    Tier2_Moderate,    // 23%
    Tier3_Cheese       // 5%
}

public class MapChokepoint
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("associated_bomb")]
    public string AssociatedBomb { get; set; } = "A"; // "A", "B", "Mid"

    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("z")]
    public float Z { get; set; }

    [JsonPropertyName("radius")]
    public float Radius { get; set; } = 350.0f;

    [JsonPropertyName("synonyms")]
    public List<string> Synonyms { get; set; } = new();
}

public class ComplementarySpotPair
{
    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("spot_anchor")]
    public string SpotAnchor { get; set; } = string.Empty;

    [JsonPropertyName("spot_support")]
    public string SpotSupport { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public class MapProfile
{
    [JsonPropertyName("map_name")]
    public string MapName { get; set; } = "de_mirage";

    [JsonPropertyName("friendly_name")]
    public string FriendlyName { get; set; } = "Mirage";

    [JsonPropertyName("chokepoints")]
    public List<MapChokepoint> Chokepoints { get; set; } = new();

    [JsonPropertyName("spots")]
    public List<TacticalSpot> Spots { get; set; } = new();

    [JsonPropertyName("crossfire_pairs")]
    public List<ComplementarySpotPair> CrossfirePairs { get; set; } = new();

    [JsonPropertyName("voice_synonyms")]
    public Dictionary<string, string> VoiceSynonyms { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}

public class ChokepointBlockState
{
    public string ChokepointId { get; set; } = string.Empty;
    public string BlockType { get; set; } = "Smoke"; // "Smoke", "Molotov"
    public float BlockedUntilTime { get; set; }
    public int PlacedByBotSlot { get; set; } = -1;

    public bool IsActive(float currentTime) => currentTime < BlockedUntilTime;
    public bool IsExpiringSoon(float currentTime) => currentTime >= (BlockedUntilTime - 2.5f) && currentTime < BlockedUntilTime;
}

public class TacticalPlayDecision
{
    public PlayTier Tier { get; set; } = PlayTier.Tier1_Standard;
    public string PlayId { get; set; } = "STANDARD_HOLD";
    public string PlayName { get; set; } = "Jogo Padrão Posicional";
    public string Description { get; set; } = "Controle posicional padrão e contenção.";
    public RoundTempo Tempo { get; set; } = RoundTempo.SLOW_DEFAULT;
    public CtDuoPlayType CtDuo { get; set; } = CtDuoPlayType.None;
    public TrTacticType TrTactic { get; set; } = TrTacticType.Default;

    public bool IsCheesePlay => Tier == PlayTier.Tier3_Cheese;
    public RoundTempo SuggestedTempo => Tempo;
    public float StagingDuration => Tier == PlayTier.Tier3_Cheese ? 5.0f : (Tempo == RoundTempo.SLOW_DEFAULT ? 18.0f : 12.0f);
}

public class TacticalSpot
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("side")]
    public string Side { get; set; } = "CT"; // "CT", "TR", "ANY"

    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("z")]
    public float Z { get; set; }

    [JsonPropertyName("pitch")]
    public float Pitch { get; set; }

    [JsonPropertyName("yaw")]
    public float Yaw { get; set; }

    [JsonPropertyName("recommended_stance")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EngagementStance RecommendedStance { get; set; } = EngagementStance.PASSIVE_HOLD;

    [JsonPropertyName("is_off_angle")]
    public bool IsOffAngle { get; set; } = false;

    [JsonPropertyName("fallback_spot_id")]
    public string? FallbackSpotId { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public class RoundHistoryItem
{
    public int RoundNumber { get; set; }
    public CsTeam Winner { get; set; }
    public string WinReason { get; set; } = string.Empty;
    public string? PlantedSite { get; set; }
    public string TacticUsed { get; set; } = string.Empty;
    public RoundTempo TempoUsed { get; set; } = RoundTempo.SLOW_DEFAULT;
}

public class BotTacticalOrder
{
    [JsonPropertyName("target_area")]
    public string TargetArea { get; set; } = "Bombsite A";

    [JsonPropertyName("role_action")]
    public string RoleAction { get; set; } = "Take position";

    [JsonPropertyName("staging_spot_id")]
    public string StagingSpotId { get; set; } = string.Empty;

    [JsonPropertyName("execute_spot_id")]
    public string ExecuteSpotId { get; set; } = string.Empty;

    [JsonPropertyName("stance")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EngagementStance Stance { get; set; } = EngagementStance.PASSIVE_HOLD;

    [JsonPropertyName("fallback_spot_id")]
    public string FallbackSpotId { get; set; } = string.Empty;

    [JsonPropertyName("required_utilities")]
    public List<string> RequiredUtilities { get; set; } = new();

    [JsonPropertyName("aggression_level")]
    public string AggressionLevel { get; set; } = "medium";

    [JsonPropertyName("mid_round_action")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public MidRoundAction MidRoundAction { get; set; } = MidRoundAction.NORMAL;

    [JsonIgnore]
    public bool IsFallingBack { get; set; } = false;

    [JsonIgnore]
    public bool HoldSiteLocked { get; set; } = false;

    [JsonIgnore]
    public bool IsNoiseGroup { get; set; } = false;

    [JsonIgnore]
    public bool HasBomb { get; set; } = false;

    [JsonIgnore]
    public bool IsWatchingFlank { get; set; } = false;
}

public class TacticalPlan
{
    [JsonPropertyName("tactic_name")]
    public string TacticName { get; set; } = "Padrão Tático Cadenciado";

    [JsonPropertyName("tactic_summary")]
    public string TacticSummary { get; set; } = "Controle de mapa inicial e execução coordenada.";

    [JsonPropertyName("round_tempo")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public RoundTempo RoundTempo { get; set; } = RoundTempo.SLOW_DEFAULT;

    [JsonPropertyName("staging_duration_seconds")]
    public float StagingDurationSeconds { get; set; } = 18.0f;

    [JsonPropertyName("tr_tactic_type")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public TrTacticType TrTacticType { get; set; } = TrTacticType.Default;

    [JsonPropertyName("ct_duo_play")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public CtDuoPlayType CtDuoPlay { get; set; } = CtDuoPlayType.None;

    [JsonIgnore]
    public PlayTier PlayTier { get; set; } = PlayTier.Tier1_Standard;

    [JsonIgnore]
    public string PlayId { get; set; } = "STANDARD_HOLD";

    [JsonIgnore]
    public RoundPhase CurrentPhase { get; set; } = RoundPhase.FreezeTime;

    [JsonIgnore]
    public AlertLevel CurrentAlertLevel { get; set; } = AlertLevel.Level0_Default;

    [JsonIgnore]
    public string? FakeTargetSite { get; set; }

    [JsonIgnore]
    public string? RealTargetSite { get; set; }

    [JsonIgnore]
    public bool IsClockDesperationActive { get; set; } = false;

    [JsonIgnore]
    public bool IsLateRoundSilenceActive { get; set; } = false;

    [JsonIgnore]
    public bool IsTacticalSaveActive { get; set; } = false;

    [JsonIgnore]
    public bool IsHeroicAttempt { get; set; } = false;

    [JsonIgnore]
    public bool IsHumanPositionLocked { get; set; } = false;

    [JsonIgnore]
    public string HumanLockedSector { get; set; } = string.Empty;

    [JsonIgnore]
    public bool IsFlankCoverActive { get; set; } = false;

    [JsonIgnore]
    public string FlankCoverSpotId { get; set; } = string.Empty;

    [JsonPropertyName("bot_orders")]
    public Dictionary<string, BotTacticalOrder> BotOrders { get; set; } = new();

    [JsonIgnore]
    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    [JsonIgnore]
    public bool IsCustomPlayerCall { get; set; } = false;
}

public class VoiceCommandPayload
{
    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;

    [JsonPropertyName("intent")]
    public string? Intent { get; set; }

    [JsonPropertyName("confidence")]
    public float Confidence { get; set; } = 1.0f;

    [JsonPropertyName("timestamp")]
    public long Timestamp { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
}
