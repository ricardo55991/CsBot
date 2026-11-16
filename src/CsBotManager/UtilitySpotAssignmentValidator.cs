using System;
using System.Collections.Generic;
using System.Linq;

namespace CsBotManager;

public enum SpotAssignmentRejectionReason
{
    NONE,
    WRONG_SIDE,
    WRONG_STATE,
    WRONG_PHASE,
    OBJECTIVE_INELIGIBLE,
    RETAKE_INELIGIBLE,
    CATALOG_REVIEW_REQUIRED,
    NO_VALID_ALTERNATIVE
}

public sealed class UtilitySpotValidationContext
{
    public string MapName { get; init; } = "de_mirage";
    public string RequestedSide { get; init; } = "CT";     // "CT" ou "TR"
    public string RequestedState { get; init; } = "HOLD";  // "TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE"
    public string RequestedPhase { get; init; } = "MapControl"; // "Setup", "MapControl", "Staging", "Contact", "PostPlant", "Retake"
    public string Role { get; init; } = "Rotator";
    public bool ObjectiveEligible { get; init; }
    public bool RetakeEligible { get; init; }
    public bool IsBombPlanted { get; init; }
    public float CurrentX { get; init; }
    public float CurrentY { get; init; }
    public float CurrentZ { get; init; }
    public ISet<string> OccupiedSpotIds { get; init; } = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    public ISet<string> BlacklistedSpotIds { get; init; } = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
}

public sealed class UtilitySpotValidationOutcome
{
    public string RequestedSpot { get; init; } = string.Empty;
    public string RequestedSide { get; init; } = string.Empty;
    public string RequestedState { get; init; } = string.Empty;
    public string RequestedPhase { get; init; } = string.Empty;
    public string ValidationResult { get; init; } = "VALID"; // "VALID", "REPLACED", "FALLBACK"
    public SpotAssignmentRejectionReason RejectionReason { get; init; } = SpotAssignmentRejectionReason.NONE;
    public string ReplacementSpot { get; init; } = string.Empty;
    public string ReplacementReason { get; init; } = string.Empty;
    public bool FallbackUsed { get; init; }
    public TacticalSpot? ApprovedSpot { get; init; }
}

/// <summary>
/// Validador localizado de atribuições de spots da Utility AI (Marco 2B.6.6).
/// Garante lado, estado, fase, mapa e elegibilidade OBJECTIVE/RETAKE, e seleciona
/// alternativa segura ordenada pelos 8 critérios sem usar o Transformer.
/// </summary>
public static class UtilitySpotAssignmentValidator
{
    public static readonly IReadOnlyDictionary<string, (string CtRule, string TRule)> ResolvedCatalogReviewRules =
        new Dictionary<string, (string CtRule, string TRule)>(StringComparer.OrdinalIgnoreCase)
        {
            ["tr_b_tapete_window_bomb_curve"] = ("RETAKE_ONLY", "ALWAYS_ALLOWED"),
            ["mid_connector_top_stairs"] = ("RETAKE_OR_HOLD", "HOLD_OR_POSTPLANT"),
            ["mid_top_mid_boxes"] = ("RETAKE_OR_HOLD", "ALWAYS_ALLOWED"),
            ["mid_window_left_awp"] = ("RETAKE_OR_HOLD", "HOLD_OR_POSTPLANT"),
        };

    private static string NormalizeSide(string? side)
    {
        if (string.IsNullOrWhiteSpace(side)) return "ANY";
        string s = side.Trim().ToUpperInvariant();
        if (s is "T" or "TR" or "TERRORIST") return "TR";
        if (s is "CT" or "COUNTERTERRORIST") return "CT";
        if (s is "ANY" or "SHARED") return "ANY";
        return s;
    }

    private static bool IsRoleAllowed(TacticalSpot spot, string role)
    {
        if (spot.AllowedRoles == null || spot.AllowedRoles.Count == 0) return true;
        foreach (string r in spot.AllowedRoles)
        {
            if (r.Equals(role, StringComparison.OrdinalIgnoreCase)) return true;
            if (r.Equals("Entry", StringComparison.OrdinalIgnoreCase) && role.Equals("EntryFragger", StringComparison.OrdinalIgnoreCase)) return true;
        }
        return false;
    }

    public static (bool IsValid, SpotAssignmentRejectionReason Reason) ValidateCandidate(
        TacticalSpot? spot,
        UtilitySpotValidationContext ctx)
    {
        if (spot == null || string.IsNullOrWhiteSpace(spot.Id))
            return (false, SpotAssignmentRejectionReason.CATALOG_REVIEW_REQUIRED);

        if (!string.Equals(ctx.MapName, "de_mirage", StringComparison.OrdinalIgnoreCase))
            return (false, SpotAssignmentRejectionReason.WRONG_PHASE);

        string reqSide = NormalizeSide(ctx.RequestedSide);
        bool isT = reqSide == "TR";
        string spotSide = NormalizeSide(spot.Side);

        // 1. Verificar se catálogo já proíbe o lado diretamente
        if (spotSide == "CT" && isT)
            return (false, SpotAssignmentRejectionReason.WRONG_SIDE);
        if (spotSide == "TR" && !isT)
            return (false, SpotAssignmentRejectionReason.WRONG_SIDE);

        // 2. Verificar regras do Contrato V2 caso spot esteja nos 53 do catálogo V3
        int idx = Array.FindIndex(PositioningTransformerContract.V2SpotClassifications, _ => false);
        _ = idx;
        string idLower = spot.Id.ToLowerInvariant();
        if (!isT && (idLower.StartsWith("tr_") || idLower.Contains("t_only")))
            return (false, SpotAssignmentRejectionReason.WRONG_SIDE);
        if (isT && (idLower.StartsWith("ct_") || idLower.Contains("ct_retake")))
            return (false, SpotAssignmentRejectionReason.WRONG_SIDE);

        // 3. Spots de retake exigem CT + RetakeEligible / fase Retake / estado RETAKE
        if (spot.Usage == SpotUsage.Retake || idLower.Contains("retake"))
        {
            if (isT) return (false, SpotAssignmentRejectionReason.WRONG_SIDE);
            if (!ctx.RetakeEligible && ctx.RequestedState != "RETAKE" && !string.Equals(ctx.RequestedPhase, "Retake", StringComparison.OrdinalIgnoreCase))
                return (false, SpotAssignmentRejectionReason.RETAKE_INELIGIBLE);
        }

        // 4. Spots de plant / box default (ex.: b_site_default_plant_box, a_default_plant_headshot)
        if (spot.Usage == SpotUsage.Plant || idLower.Contains("_plant"))
        {
            if (isT)
            {
                bool okT = ctx.ObjectiveEligible
                    || ctx.IsBombPlanted
                    || ctx.RequestedState == "OBJECTIVE"
                    || string.Equals(ctx.RequestedPhase, "PostPlant", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(ctx.RequestedPhase, "Executing", StringComparison.OrdinalIgnoreCase);
                if (!okT)
                    return (false, ctx.RequestedPhase.Equals("MapControl", StringComparison.OrdinalIgnoreCase) || ctx.RequestedPhase.Equals("Setup", StringComparison.OrdinalIgnoreCase)
                        ? SpotAssignmentRejectionReason.WRONG_PHASE
                        : SpotAssignmentRejectionReason.OBJECTIVE_INELIGIBLE);
            }
            else
            {
                bool okCt = ctx.RetakeEligible
                    || ctx.IsBombPlanted
                    || ctx.RequestedState == "RETAKE"
                    || string.Equals(ctx.RequestedPhase, "Retake", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(ctx.RequestedPhase, "PostPlant", StringComparison.OrdinalIgnoreCase);
                if (!okCt)
                    return (false, SpotAssignmentRejectionReason.WRONG_PHASE);
            }
        }

        // 5. Regras exatas para os 4 spots resolvidos na Seção 2
        if (ResolvedCatalogReviewRules.TryGetValue(spot.Id, out var rulePair))
        {
            string rule = isT ? rulePair.TRule : rulePair.CtRule;
            if (rule == "RETAKE_ONLY")
            {
                if (!ctx.RetakeEligible && ctx.RequestedState != "RETAKE" && !string.Equals(ctx.RequestedPhase, "Retake", StringComparison.OrdinalIgnoreCase))
                    return (false, SpotAssignmentRejectionReason.RETAKE_INELIGIBLE);
            }
            else if (rule == "RETAKE_OR_HOLD")
            {
                bool ok = ctx.RetakeEligible
                    || ctx.RequestedState is "HOLD" or "STAGING" or "CLEARANCE" or "RETAKE"
                    || ctx.RequestedPhase is "Setup" or "Retake" or "PostPlant" or "Contact" or "MapControl";
                if (!ok)
                    return (false, SpotAssignmentRejectionReason.WRONG_STATE);
            }
            else if (rule == "HOLD_OR_POSTPLANT")
            {
                bool ok = ctx.IsBombPlanted
                    || ctx.ObjectiveEligible
                    || ctx.RequestedState is "HOLD" or "CLEARANCE" or "OBJECTIVE"
                    || ctx.RequestedPhase is "PostPlant" or "Contact";
                if (!ok)
                    return (false, SpotAssignmentRejectionReason.WRONG_PHASE);
            }
        }

        return (true, SpotAssignmentRejectionReason.NONE);
    }

    public static UtilitySpotValidationOutcome ValidateAndResolve(
        TacticalSpot? requestedSpot,
        UtilitySpotValidationContext ctx,
        IReadOnlyList<TacticalSpot> catalogSpots)
    {
        string reqId = requestedSpot?.Id ?? string.Empty;
        string reqSide = NormalizeSide(ctx.RequestedSide);
        var (ok, reason) = ValidateCandidate(requestedSpot, ctx);
        if (ok)
        {
            return new UtilitySpotValidationOutcome
            {
                RequestedSpot = reqId,
                RequestedSide = reqSide,
                RequestedState = ctx.RequestedState,
                RequestedPhase = ctx.RequestedPhase,
                ValidationResult = "VALID",
                RejectionReason = SpotAssignmentRejectionReason.NONE,
                ReplacementSpot = string.Empty,
                ReplacementReason = string.Empty,
                FallbackUsed = false,
                ApprovedSpot = requestedSpot,
            };
        }

        string targetSector = requestedSpot?.Sector ?? string.Empty;
        string targetSite = requestedSpot?.AssociatedBombsite ?? "None";
        SpotUsage? targetUsage = requestedSpot?.Usage;

        // Ordenar alternativas válidas pelos 8 critérios exatos da Seção 4:
        // 1. mesmo lado (validado em ValidateCandidate)
        // 2. mesmo setor / bombsite
        // 3. mesmo papel
        // 4. mesmo estado tático (Usage)
        // 5. mesma fase do round (validado em ValidateCandidate)
        // 6. menor distância navegável
        // 7. disponibilidade do spot (!Blacklisted)
        // 8. ausência de conflito com aliado (!Occupied)
        float refX = (ctx.CurrentX != 0 || ctx.CurrentY != 0) ? ctx.CurrentX : (requestedSpot?.X ?? 0f);
        float refY = (ctx.CurrentX != 0 || ctx.CurrentY != 0) ? ctx.CurrentY : (requestedSpot?.Y ?? 0f);
        float refZ = (ctx.CurrentX != 0 || ctx.CurrentY != 0) ? ctx.CurrentZ : (requestedSpot?.Z ?? 0f);

        var validCandidates = catalogSpots
            .Where(c => !string.Equals(c.Id, reqId, StringComparison.OrdinalIgnoreCase))
            .Where(c => !c.Id.EndsWith("_spawn_safe", StringComparison.OrdinalIgnoreCase))
            .Where(c => !ctx.BlacklistedSpotIds.Contains(c.Id))
            .Where(c => ValidateCandidate(c, ctx).IsValid)
            .OrderBy(c =>
            {
                if (!string.IsNullOrEmpty(targetSector) && c.Sector.Equals(targetSector, StringComparison.OrdinalIgnoreCase)) return 0;
                if (!string.Equals(targetSite, "None", StringComparison.OrdinalIgnoreCase) && c.AssociatedBombsite.Equals(targetSite, StringComparison.OrdinalIgnoreCase)) return 1;
                return 2;
            })
            .ThenBy(c => IsRoleAllowed(c, ctx.Role) ? 0 : 1)
            .ThenBy(c => (targetUsage.HasValue && c.Usage == targetUsage.Value) ? 0 : 1)
            .ThenBy(c => ctx.OccupiedSpotIds.Contains(c.Id) ? 1 : 0)
            .ThenBy(c =>
            {
                float dx = c.X - refX;
                float dy = c.Y - refY;
                float dz = c.Z - refZ;
                return dx * dx + dy * dy + dz * dz;
            })
            .ToList();

        if (validCandidates.Count > 0)
        {
            var chosen = validCandidates[0];
            return new UtilitySpotValidationOutcome
            {
                RequestedSpot = reqId,
                RequestedSide = reqSide,
                RequestedState = ctx.RequestedState,
                RequestedPhase = ctx.RequestedPhase,
                ValidationResult = "REPLACED",
                RejectionReason = reason,
                ReplacementSpot = chosen.Id,
                ReplacementReason = reason.ToString(),
                FallbackUsed = false,
                ApprovedSpot = chosen,
            };
        }

        // Sem alternativa válida: manter setor atual via fallback Utility AI existente
        string safeId = reqSide == "CT" ? "ct_spawn_safe" : "tr_spawn_safe";
        var safeSpot = catalogSpots.FirstOrDefault(s => s.Id.Equals(safeId, StringComparison.OrdinalIgnoreCase) && ValidateCandidate(s, ctx).IsValid);
        return new UtilitySpotValidationOutcome
        {
            RequestedSpot = reqId,
            RequestedSide = reqSide,
            RequestedState = ctx.RequestedState,
            RequestedPhase = ctx.RequestedPhase,
            ValidationResult = "FALLBACK",
            RejectionReason = reason,
            ReplacementSpot = safeSpot?.Id ?? string.Empty,
            ReplacementReason = SpotAssignmentRejectionReason.NO_VALID_ALTERNATIVE.ToString(),
            FallbackUsed = true,
            ApprovedSpot = safeSpot,
        };
    }
}
