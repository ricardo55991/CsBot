using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

namespace CsBotManager;

public enum PositioningStateKind
{
    TRANSIT = 0,
    CLEARANCE = 1,
    STAGING = 2,
    HOLD = 3,
    OBJECTIVE = 4,
    RETAKE = 5
}

public enum SectorTransitionKind
{
    NO_TRANSITION = 0,
    TRANSITION_OCCURS = 1
}

public enum NextSectorKind
{
    A = 0,
    B = 1,
    MID = 2,
    CT = 3,
    T = 4
}

public enum TransitionKind
{
    ADVANCE = 0,
    HOLD = 1,
    FALLBACK = 2,
    ROTATE = 3,
    CONVERGE = 4,
    COVER = 5,
    LURK = 6
}

public enum ExitTriggerKind
{
    TIME = 0,
    CONTACT = 1,
    FIRST_KILL = 2,
    TEAMMATE_DEATH = 3,
    BOMB_SPOTTED = 4,
    BOMB_PLANTED = 5,
    UTILITY_EXPIRED = 6,
    TACTIC_REVISION = 7
}

public static class PositioningTransformerContract
{
    public const string ContractVersion = "positioning_runtime_contract_v1";
    public const int SequenceLength = 32;
    public const int FeatureCount = 18;
    public const int TeammateSlots = 4;
    public const int CandidateSpotCount = 53;
    public const int NeuralStateCount = 6;
    public const float SectorTransitionThreshold = 0.525f;
    public const int DefaultCadenceHz = 4;
    public const int DefaultPreferredBatchSize = 5;
    public const int DefaultMaxBatchWaitMs = 5;
    public const int DefaultInferenceTimeoutMs = 25;
    public const int DefaultMaxPendingRequests = 4;

    public static readonly string[] ExpectedInputNames =
    {
        "self_history",
        "teammates",
        "temporal_mask",
        "teammate_mask",
        "candidate_mask",
        "objective_eligible",
        "retake_eligible"
    };

    public static readonly string[] ExpectedInputNamesV2 =
    {
        "self_history",
        "teammates",
        "temporal_mask",
        "teammate_mask",
        "candidate_mask",
        "objective_eligible",
        "retake_eligible",
        "team_idx",
        "role_idx",
        "stage_idx"
    };

    // Mapeamentos congelados idênticos ao Python (canonical_temporal_dataloader.py)
    public static readonly IReadOnlyDictionary<string, long> TeamMap = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase)
    {
        ["CT"] = 0,
        ["TR"] = 1,
        ["T"] = 1,
        ["ANY"] = 2,
    };

    public static readonly string[] RoleNames =
    {
        "SUPPORT", "BOMB_CARRIER", "SECOND_ENTRY", "ANCHOR", "RETAKE_ENTRY",
        "ENTRY", "LURKER", "AWPER", "ROTATOR", "RETAKE_COVER"
    };

    public static readonly IReadOnlyDictionary<string, long> RoleMap = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase)
    {
        ["SUPPORT"] = 0,
        ["BOMB_CARRIER"] = 1,
        ["SECOND_ENTRY"] = 2,
        ["ANCHOR"] = 3,
        ["RETAKE_ENTRY"] = 4,
        ["ENTRY"] = 5,
        ["LURKER"] = 6,
        ["AWPER"] = 7,
        ["ROTATOR"] = 8,
        ["RETAKE_COVER"] = 9,
    };

    public static readonly string[] StageNames =
    {
        "MapControl", "Staging", "Contact", "Setup", "PostPlant", "Retake"
    };

    public static readonly IReadOnlyDictionary<string, long> StageMap = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase)
    {
        ["MapControl"] = 0,
        ["Staging"] = 1,
        ["Contact"] = 2,
        ["Setup"] = 3,
        ["PostPlant"] = 4,
        ["Retake"] = 5,
    };

    public static long MapTeamToIndex(int teamNum, out bool usedFallback)
    {
        if (teamNum == 3) { usedFallback = false; return 0; } // CT
        if (teamNum == 2) { usedFallback = false; return 1; } // TR
        usedFallback = true;
        return 2; // ANY fallback explícito
    }

    public static long MapTeamNameToIndex(string? teamName, out bool usedFallback)
    {
        if (!string.IsNullOrWhiteSpace(teamName) && TeamMap.TryGetValue(teamName.Trim(), out long idx))
        {
            usedFallback = false;
            return idx;
        }
        usedFallback = true;
        return 2; // ANY fallback explícito
    }

    public static long MapRoleToIndex(string? roleName, out bool usedFallback)
    {
        if (!string.IsNullOrWhiteSpace(roleName) && RoleMap.TryGetValue(roleName.Trim(), out long idx))
        {
            usedFallback = false;
            return idx;
        }
        usedFallback = true;
        return 0; // SUPPORT fallback explícito
    }

    public static long MapStageToIndex(string? stageName, out bool usedFallback)
    {
        if (!string.IsNullOrWhiteSpace(stageName) && StageMap.TryGetValue(stageName.Trim(), out long idx))
        {
            usedFallback = false;
            return idx;
        }
        usedFallback = true;
        return 0; // MapControl fallback explícito
    }

    /// <summary>
    /// Deriva o estágio tático estritamente a partir de estado causal atual/passado do round/plano,
    /// sem usar informação futura e sem reutilizar PositioningState previsto.
    /// </summary>
    public static string DeriveCausalStageName(
        bool isBombPlanted,
        bool isTerrorist,
        bool isFreezeTime,
        bool hasSeenEnemyRecently,
        bool inSiteOrObjectiveZone)
    {
        if (isBombPlanted)
        {
            return isTerrorist ? "PostPlant" : "Retake";
        }
        if (isFreezeTime)
        {
            return "Setup";
        }
        if (hasSeenEnemyRecently)
        {
            return "Contact";
        }
        if (inSiteOrObjectiveZone)
        {
            return isTerrorist ? "Staging" : "Setup";
        }
        return "MapControl";
    }

    public static readonly string[] ExpectedOutputNames =
    {
        "final_state_logits",
        "final_state_id",
        "sector_transition_logits",
        "sector_transition_id",
        "next_sector_logits",
        "next_sector_id",
        "spot_logits",
        "selected_spot_id",
        "transition_logits",
        "transition_id",
        "exit_trigger_logits",
        "exit_trigger_id",
        "confidence_by_head"
    };

    // 27 spots supervisionados do catálogo Mirage v3 (supervised_spot_mask_v1.json)
    public static readonly bool[] DefaultSupervisedSpotMask = BuildDefaultSupervisedSpotMask();

    // Side-aware masks do contrato spot_side_contract_v1.json (CT_ONLY=26, T_ONLY=11, SHARED=16)
    public static readonly bool[] CtAllowedSpotMask =
    {
        true,true,true,true,false,true,true,true,true,true,true,true,true,false,false,false,false,true,true,true,true,true,true,true,true,true,true,true,true,false,false,true,true,true,true,false,true,true,false,false,true,true,true,true,true,true,true,true,true,false,true,true,true
    };

    public static readonly bool[] TAllowedSpotMask =
    {
        true,true,true,true,true,false,true,false,false,false,false,false,false,true,true,true,true,false,false,false,false,false,false,false,false,false,false,true,true,true,true,true,false,false,true,true,true,true,true,true,false,false,false,false,true,true,true,true,true,true,false,false,false
    };

    public static bool[] BuildSideAwareCandidateMask(bool isTerrorist, bool[]? baseMask = null)
    {
        var sideMask = isTerrorist ? TAllowedSpotMask : CtAllowedSpotMask;
        var res = new bool[CandidateSpotCount];
        for (int i = 0; i < CandidateSpotCount; i++)
        {
            res[i] = sideMask[i] && (baseMask == null || i >= baseMask.Length || baseMask[i]);
        }
        return res;
    }

    // Contrato V2 (spot_side_contract_v2.json):
    // Classificação: SHARED, CT_ONLY, T_ONLY, CONTEXTUAL, CATALOG_REVIEW_REQUIRED
    public static readonly string[] V2SpotClassifications =
    {
        "SHARED","SHARED","SHARED","SHARED","T_ONLY","CT_ONLY","CONTEXTUAL","CT_ONLY","CT_ONLY","CT_ONLY",
        "CT_ONLY","CT_ONLY","CT_ONLY","SHARED","CATALOG_REVIEW_REQUIRED","T_ONLY","T_ONLY","CONTEXTUAL","CT_ONLY","CONTEXTUAL",
        "CT_ONLY","CT_ONLY","CONTEXTUAL","CT_ONLY","CONTEXTUAL","CONTEXTUAL","CONTEXTUAL","SHARED","SHARED","T_ONLY",
        "T_ONLY","SHARED","SHARED","CATALOG_REVIEW_REQUIRED","SHARED","CATALOG_REVIEW_REQUIRED","SHARED","SHARED","SHARED","SHARED",
        "SHARED","CT_ONLY","SHARED","CATALOG_REVIEW_REQUIRED","SHARED","SHARED","SHARED","SHARED","CONTEXTUAL","SHARED",
        "CONTEXTUAL","SHARED","CT_ONLY"
    };

    public static readonly string[] V2CtRules =
    {
        "ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","FORBIDDEN","ALWAYS_ALLOWED","RETAKE_ONLY","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD",
        "RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","ALWAYS_ALLOWED","ALLOWED","FORBIDDEN","FORBIDDEN","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD",
        "RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","RETAKE_OR_HOLD","ALWAYS_ALLOWED","ALWAYS_ALLOWED","FORBIDDEN",
        "FORBIDDEN","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED",
        "ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","RETAKE_ONLY","ALWAYS_ALLOWED",
        "RETAKE_OR_HOLD","ALWAYS_ALLOWED","ALWAYS_ALLOWED"
    };

    public static readonly string[] V2TRules =
    {
        "ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","FORBIDDEN","OBJECTIVE_OR_POSTPLANT","FORBIDDEN","FORBIDDEN","FORBIDDEN",
        "FORBIDDEN","FORBIDDEN","FORBIDDEN","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALLOWED_SHARED_GEOMETRY_ONLY","FORBIDDEN","ALLOWED_SHARED_GEOMETRY_ONLY",
        "FORBIDDEN","FORBIDDEN","ALLOWED_SHARED_GEOMETRY_ONLY","FORBIDDEN","ALLOWED_SHARED_GEOMETRY_ONLY","ALLOWED_SHARED_GEOMETRY_ONLY","ALLOWED_SHARED_GEOMETRY_ONLY","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED",
        "ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","FORBIDDEN","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED",
        "ALWAYS_ALLOWED","FORBIDDEN","ALWAYS_ALLOWED","ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","ALWAYS_ALLOWED","OBJECTIVE_OR_POSTPLANT","ALWAYS_ALLOWED",
        "ALLOWED_SHARED_GEOMETRY_ONLY","ALWAYS_ALLOWED","FORBIDDEN"
    };

    /// <summary>
    /// Constrói a máscara em camadas do Contrato V2 (supervised_spot_mask -> side_mask -> state_mask -> phase_mask).
    /// </summary>
    public static bool[] BuildV2CandidateMask(
        bool isTerrorist,
        string? positioningState = null,
        bool objectiveEligible = false,
        bool retakeEligible = false,
        bool[]? supervisedMask = null)
    {
        var res = new bool[CandidateSpotCount];
        for (int i = 0; i < CandidateSpotCount; i++)
        {
            if (supervisedMask != null && i < supervisedMask.Length && !supervisedMask[i])
            {
                res[i] = false;
                continue;
            }

            string cls = V2SpotClassifications[i];
            string rule = isTerrorist ? V2TRules[i] : V2CtRules[i];

            if (rule == "FORBIDDEN")
            {
                res[i] = false;
                continue;
            }

            if (cls == "CONTEXTUAL")
            {
                if (rule == "RETAKE_ONLY" && !retakeEligible)
                {
                    res[i] = false;
                    continue;
                }
                if (rule == "OBJECTIVE_OR_POSTPLANT"
                    && !objectiveEligible
                    && positioningState != "OBJECTIVE"
                    && positioningState != "HOLD")
                {
                    res[i] = false;
                    continue;
                }
                if (rule == "RETAKE_OR_HOLD"
                    && !retakeEligible
                    && positioningState != "HOLD"
                    && positioningState != "STAGING"
                    && positioningState != "CLEARANCE")
                {
                    res[i] = false;
                    continue;
                }
            }

            res[i] = true;
        }
        return res;
    }

    private static bool[] BuildDefaultSupervisedSpotMask()
    {
        var mask = new bool[CandidateSpotCount];
        // Caso o JSON não seja fornecido explicitamente, inicializa todos como true
        // (em runtime real e testes específicos o mask de 27/53 pode ser injetado).
        for (int i = 0; i < mask.Length; i++) mask[i] = true;
        return mask;
    }

    public static string PseudonymizePlayerSlot(int slot, string? matchSalt = null)
    {
        string raw = $"{matchSalt ?? "csbot"}:slot:{slot}";
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return Convert.ToHexString(hash, 0, 6).ToLowerInvariant();
    }
}

public sealed class PositioningShadowInferenceInput
{
    public int BatchSize { get; init; }
    public string MapName { get; init; } = "de_mirage";
    public int RoundId { get; init; }
    public bool HasRoundBoundaryCrossing { get; init; }
    public float[] SelfHistory { get; init; } = Array.Empty<float>();       // [B * 32 * 18]
    public float[] Teammates { get; init; } = Array.Empty<float>();         // [B * 32 * 4 * 18]
    public float[] TemporalMask { get; init; } = Array.Empty<float>();      // [B * 32]
    public float[] TeammateMask { get; init; } = Array.Empty<float>();      // [B * 32 * 4]
    public bool[] CandidateMask { get; init; } = Array.Empty<bool>();       // [B * 53]
    public bool[] ObjectiveEligible { get; init; } = Array.Empty<bool>();   // [B]
    public bool[] RetakeEligible { get; init; } = Array.Empty<bool>();      // [B]
    public bool[] PlayerAlive { get; init; } = Array.Empty<bool>();         // [B]
    public long[] TeamIdx { get; init; } = Array.Empty<long>();             // [B] int64 (opcional em V1, obrigatório em V2)
    public long[] RoleIdx { get; init; } = Array.Empty<long>();             // [B] int64
    public long[] StageIdx { get; init; } = Array.Empty<long>();            // [B] int64
    public int ContextFallbackCount { get; init; }
}

public sealed class PositioningShadowPrediction
{
    public bool InputValid { get; init; }
    public bool InferenceSuccess { get; init; }
    public PositioningStateKind? FinalState { get; init; }
    public SectorTransitionKind? SectorTransition { get; init; }
    public NextSectorKind? NextSector { get; init; }
    public int? SelectedSpotId { get; init; }
    public TransitionKind? Transition { get; init; }
    public ExitTriggerKind? ExitTrigger { get; init; }
    public float[] ConfidenceByHead { get; init; } = new float[6];
    public bool SaveFallbackActive { get; init; } = true;
    public string FallbackReason { get; init; } = string.Empty;
    public double LatencyMs { get; init; }
}

public static class PositioningInputValidator
{
    public static (bool IsValid, string Reason) Validate(PositioningShadowInferenceInput input)
    {
        if (input == null) return (false, "INPUT_NULL");
        if (!string.Equals(input.MapName, "de_mirage", StringComparison.OrdinalIgnoreCase))
            return (false, "NON_MIRAGE_MAP_SKIPPED");
        if (input.HasRoundBoundaryCrossing)
            return (false, "ROUND_BOUNDARY_CROSSING");
        int b = input.BatchSize;
        if (b <= 0) return (false, "INPUT_CONTRACT_REJECTED_EMPTY_BATCH");

        if (input.SelfHistory.Length != b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.FeatureCount)
            return (false, "INPUT_CONTRACT_REJECTED_SELF_HISTORY_SHAPE");
        if (input.Teammates.Length != b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots * PositioningTransformerContract.FeatureCount)
            return (false, "INPUT_CONTRACT_REJECTED_TEAMMATES_SHAPE");
        if (input.TemporalMask.Length != b * PositioningTransformerContract.SequenceLength)
            return (false, "INPUT_CONTRACT_REJECTED_TEMPORAL_MASK_SHAPE");
        if (input.TeammateMask.Length != b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots)
            return (false, "INPUT_CONTRACT_REJECTED_TEAMMATE_MASK_SHAPE");
        if (input.CandidateMask.Length != b * PositioningTransformerContract.CandidateSpotCount)
            return (false, "INPUT_CONTRACT_REJECTED_CANDIDATE_MASK_SHAPE");
        if (input.ObjectiveEligible.Length != b || input.RetakeEligible.Length != b)
            return (false, "INPUT_CONTRACT_REJECTED_ELIGIBILITY_SHAPE");
        if (input.PlayerAlive.Length == b)
        {
            bool anyAlive = false;
            for (int i = 0; i < b; i++)
            {
                if (input.PlayerAlive[i]) { anyAlive = true; break; }
            }
            if (!anyAlive) return (false, "DEAD_PLAYER_SKIPPED");
        }

        for (int i = 0; i < input.SelfHistory.Length; i++)
        {
            if (float.IsNaN(input.SelfHistory[i]) || float.IsInfinity(input.SelfHistory[i]))
                return (false, "INPUT_CONTRACT_REJECTED_NON_FINITE_SELF");
        }
        for (int i = 0; i < input.Teammates.Length; i++)
        {
            if (float.IsNaN(input.Teammates[i]) || float.IsInfinity(input.Teammates[i]))
                return (false, "INPUT_CONTRACT_REJECTED_NON_FINITE_TEAMMATE");
        }

        // Verificar que nenhuma linha tem candidate_mask totalmente vazia
        for (int row = 0; row < b; row++)
        {
            bool anySpot = false;
            int offset = row * PositioningTransformerContract.CandidateSpotCount;
            for (int s = 0; s < PositioningTransformerContract.CandidateSpotCount; s++)
            {
                if (input.CandidateMask[offset + s]) { anySpot = true; break; }
            }
            if (!anySpot) return (false, "EMPTY_CANDIDATE_MASK");
        }

        return (true, string.Empty);
    }
}

/// <summary>
/// Proteção explícita de Shadow Mode: garante que a saída neural nunca altere a decisão real da Utility AI.
/// </summary>
public static class ShadowModeGuard
{
    public static TUtilityDecision ShadowModeCannotAffectBotDecision<TUtilityDecision>(
        TUtilityDecision authoritativeUtilityDecision,
        PositioningShadowPrediction? neuralShadowSuggestion)
    {
        // A sugestão neural é estritamente observacional/logada; jamais sobrescreve a decisão da Utility AI.
        _ = neuralShadowSuggestion;
        return authoritativeUtilityDecision;
    }
}
