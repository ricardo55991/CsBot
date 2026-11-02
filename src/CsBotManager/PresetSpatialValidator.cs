using System.Text;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum PresetValidationResult
{
    Valid,
    Rejected,
    FallbackSubstituted
}

public sealed class PresetValidationOutcome
{
    public PresetValidationResult Result { get; set; } = PresetValidationResult.Valid;
    public string InvalidField { get; set; } = string.Empty;
    public string ExpectedBombsite { get; set; } = string.Empty;
    public string ActualBombsite { get; set; } = string.Empty;
    public string ReplacementSpot { get; set; } = string.Empty;
    public string Details { get; set; } = string.Empty;
}

public sealed class PresetStartupAudit
{
    public int PresetsTotal { get; set; }
    public int PresetsValid { get; set; }
    public int PresetsInvalid { get; set; }
    public int PresetsCorrected { get; set; }
    public int MissingSpots { get; set; }
    public int IncompatibleBombsites { get; set; }
    public List<string> AuditMessages { get; } = new();

    public string FormatSummary()
    {
        var sb = new StringBuilder();
        sb.AppendLine($"[PresetSpatialValidator] Auditoria de Inicialização dos Presets:");
        sb.AppendLine($" - presets_total: {PresetsTotal}");
        sb.AppendLine($" - presets_valid: {PresetsValid}");
        sb.AppendLine($" - presets_invalid: {PresetsInvalid}");
        sb.AppendLine($" - presets_corrected: {PresetsCorrected}");
        sb.AppendLine($" - missing_spots: {MissingSpots}");
        sb.AppendLine($" - incompatible_bombsites: {IncompatibleBombsites}");
        return sb.ToString();
    }
}

public static class PresetSpatialValidator
{
    public static PresetValidationOutcome ValidateOrder(
        BotTacticalOrder order,
        BotRole role,
        string tacticName,
        string tacticBombsite, // "A", "B", "Mid"
        CsTeam team,
        bool isC4Carrier,
        bool allowCrossSiteLurk,
        bool isFakeTactic,
        MapProfileManager? mapProfileManager)
    {
        var outcome = new PresetValidationOutcome
        {
            ExpectedBombsite = tacticBombsite
        };

        if (mapProfileManager == null)
        {
            outcome.Result = PresetValidationResult.Valid;
            return outcome;
        }

        string expectedSide = team == CsTeam.CounterTerrorist ? "CT" : "TR";

        // Regra 1: SpotId existe
        var stagingSpot = mapProfileManager.GetSpotById(order.StagingSpotId);
        if (stagingSpot == null)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "StagingSpotId";
            outcome.Details = $"Staging spot '{order.StagingSpotId}' não existe no mapa.";
            return outcome;
        }

        var execSpot = mapProfileManager.GetSpotById(order.ExecuteSpotId);
        if (execSpot == null)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotId";
            outcome.Details = $"Execute spot '{order.ExecuteSpotId}' não existe no mapa.";
            return outcome;
        }

        // Regra 2: TeamSide corresponde
        if (!stagingSpot.Side.Equals(expectedSide, StringComparison.OrdinalIgnoreCase) && !stagingSpot.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase))
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "StagingSpotSide";
            outcome.Details = $"Staging spot '{stagingSpot.Id}' pertence a {stagingSpot.Side}, mas o time é {expectedSide}.";
            return outcome;
        }

        if (!execSpot.Side.Equals(expectedSide, StringComparison.OrdinalIgnoreCase) && !execSpot.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase))
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotSide";
            outcome.Details = $"Execute spot '{execSpot.Id}' pertence a {execSpot.Side}, mas o time é {expectedSide}.";
            return outcome;
        }

        // Regra 3: StagingSpot possui Usage Staging/Hold/Lurk
        if ((stagingSpot.Usage & (SpotUsage.Staging | SpotUsage.Hold | SpotUsage.Lurk | SpotUsage.Spawn)) == 0)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "StagingSpotUsage";
            outcome.Details = $"Staging spot '{stagingSpot.Id}' possui uso {stagingSpot.Usage}, incompatível com Staging/Hold/Lurk.";
            return outcome;
        }

        // Regra 4: ExecuteSpot possui Usage Execute/Plant/Cover/Hold
        if ((execSpot.Usage & (SpotUsage.Execute | SpotUsage.Plant | SpotUsage.Cover | SpotUsage.Hold | SpotUsage.Retake)) == 0)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotUsage";
            outcome.Details = $"Execute spot '{execSpot.Id}' possui uso {execSpot.Usage}, incompatível com Execute/Plant/Cover.";
            return outcome;
        }

        // Determina Bombsite do Spot
        string stagingSite = DetermineSpotBombsite(stagingSpot);
        string execSite = DetermineSpotBombsite(execSpot);
        outcome.ActualBombsite = execSite;

        // Regra 13: Não permitir Apartments B -> staging_a_ramp sem justificativa
        if (order.TargetArea.Contains("Apartments B", StringComparison.OrdinalIgnoreCase) && order.StagingSpotId.Contains("a_ramp", StringComparison.OrdinalIgnoreCase))
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "StagingSpotId";
            outcome.ExpectedBombsite = "B";
            outcome.ActualBombsite = "A";
            outcome.Details = "Apartments B associado com staging_a_ramp é proibido.";
            return outcome;
        }

        // Regra 11: C4 carrier sempre recebe execute no bombsite atual
        if (isC4Carrier && tacticBombsite != "Mid" && execSite != "Mid" && execSite != tacticBombsite)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "C4CarrierExecuteSpot";
            outcome.ExpectedBombsite = tacticBombsite;
            outcome.ActualBombsite = execSite;
            outcome.Details = $"C4 Carrier executando em {execSite}, mas a tática mira em {tacticBombsite}.";
            return outcome;
        }

        // Regra 8: Split B requer B final site; Split A requer A final site
        if (tacticName.Contains("Split B", StringComparison.OrdinalIgnoreCase) && execSite == "A")
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotBombsite";
            outcome.ExpectedBombsite = "B";
            outcome.ActualBombsite = "A";
            outcome.Details = "Split B requer execute no Bombsite B.";
            return outcome;
        }

        if (tacticName.Contains("Split A", StringComparison.OrdinalIgnoreCase) && execSite == "B")
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotBombsite";
            outcome.ExpectedBombsite = "A";
            outcome.ActualBombsite = "B";
            outcome.Details = "Split A requer execute no Bombsite A.";
            return outcome;
        }

        // Regra 6: Estratégia A não usa execute exclusivo B
        if (tacticBombsite == "A" && execSite == "B" && !isFakeTactic)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "ExecuteSpotBombsite";
            outcome.ExpectedBombsite = "A";
            outcome.ActualBombsite = "B";
            outcome.Details = "Estratégia A executando no Bombsite B sem ser fake.";
            return outcome;
        }

        // Regra 7: Estratégia B não usa execute exclusivo A
        if (tacticBombsite == "B" && execSite == "A" && !isFakeTactic)
        {
            // Regra 9: Lurker divergente precisa de AllowCrossSiteLurk=true
            if (role == BotRole.Anchor && allowCrossSiteLurk)
            {
                // Permitido lurk com flag explícita
            }
            else
            {
                outcome.Result = PresetValidationResult.Rejected;
                outcome.InvalidField = "ExecuteSpotBombsite";
                outcome.ExpectedBombsite = "B";
                outcome.ActualBombsite = "A";
                outcome.Details = "Estratégia B executando no Bombsite A sem AllowCrossSiteLurk.";
                return outcome;
            }
        }

        // Regra 9: Lurker divergente sem flag explícita
        if (execSite != tacticBombsite && execSite != "Mid" && tacticBombsite != "Mid" && !isFakeTactic && !allowCrossSiteLurk)
        {
            outcome.Result = PresetValidationResult.Rejected;
            outcome.InvalidField = "LurkerCrossSite";
            outcome.ExpectedBombsite = tacticBombsite;
            outcome.ActualBombsite = execSite;
            outcome.Details = $"Spot divergente ({execSite}) sem AllowCrossSiteLurk=true.";
            return outcome;
        }

        outcome.Result = PresetValidationResult.Valid;
        return outcome;
    }

    public static BombsiteTarget DetermineSpotBombsiteTarget(TacticalSpot spot)
    {
        if (!string.IsNullOrEmpty(spot.AssociatedBombsite) && spot.AssociatedBombsite != "None")
        {
            if (BombsiteParser.TryParseBombsiteTarget(spot.AssociatedBombsite, out var parsed))
            {
                return parsed;
            }
        }

        string s = (spot.Sector + " " + spot.Id).ToLowerInvariant();
        if (s.Contains("site b") || s.Contains("tapete") || s.Contains("apartments") || s.Contains("van") || s.Contains("_b_") || s.Contains("bomb b"))
            return BombsiteTarget.B;
        if (s.Contains("site a") || s.Contains("rampa") || s.Contains("palacio") || s.Contains("palace") || s.Contains("_a_") || s.Contains("bomb a"))
            return BombsiteTarget.A;
        if (s.Contains("mid") || s.Contains("meio") || s.Contains("window") || s.Contains("connector") || s.Contains("underpass"))
            return BombsiteTarget.Mid;

        return BombsiteTarget.None;
    }

    public static string DetermineSpotBombsite(TacticalSpot spot)
    {
        var target = DetermineSpotBombsiteTarget(spot);
        return target switch
        {
            BombsiteTarget.A => "A",
            BombsiteTarget.B => "B",
            BombsiteTarget.Mid => "Mid",
            _ => "None"
        };
    }

    public static PresetValidationOutcome ValidateAndApplyFallback(
        BotTacticalOrder order,
        BotRole role,
        string tacticName,
        string tacticBombsite,
        CsTeam team,
        bool isC4Carrier,
        bool allowCrossSiteLurk,
        bool isFakeTactic,
        MapProfileManager? mapProfileManager)
    {
        var outcome = ValidateOrder(order, role, tacticName, tacticBombsite, team, isC4Carrier, allowCrossSiteLurk, isFakeTactic, mapProfileManager);
        if (outcome.Result == PresetValidationResult.Valid || mapProfileManager == null)
        {
            return outcome;
        }

        // Regra 14: Não corrigir silenciosamente. Substitui por um spot válido do mesmo bombsite
        string sideStr = team == CsTeam.CounterTerrorist ? "CT" : "TR";
        var sameSiteSpots = mapProfileManager.GetSpotsForTeam(sideStr)
            .Where(s => DetermineSpotBombsite(s).Equals(tacticBombsite, StringComparison.OrdinalIgnoreCase))
            .ToList();

        if (sameSiteSpots.Count > 0)
        {
            var fallbackStaging = sameSiteSpots.FirstOrDefault(s => (s.Usage & (SpotUsage.Staging | SpotUsage.Hold)) != 0) ?? sameSiteSpots[0];
            var fallbackExec = sameSiteSpots.FirstOrDefault(s => (s.Usage & (SpotUsage.Execute | SpotUsage.Plant)) != 0) ?? sameSiteSpots[0];

            order.StagingSpotId = fallbackStaging.Id;
            order.ExecuteSpotId = fallbackExec.Id;
            order.TargetArea = $"Bombsite {tacticBombsite}";

            outcome.Result = PresetValidationResult.FallbackSubstituted;
            outcome.ReplacementSpot = fallbackExec.Id;
            outcome.Details = $"Preset inválido ({outcome.InvalidField}). Substituído por spot válido de Bombsite {tacticBombsite}: {fallbackExec.Id}";
        }

        return outcome;
    }

    public static PresetStartupAudit RunStartupAudit(MapProfileManager mapProfileManager, OllamaIglService iglService)
    {
        var audit = new PresetStartupAudit();
        var tacticsToTest = new List<(string Name, string Bombsite, CsTeam Team, bool IsFake)>
        {
            ("Padrão 2-1-2 A/B Retake", "A", CsTeam.CounterTerrorist, false),
            ("Execução Rápida A", "A", CsTeam.Terrorist, false),
            ("Execução B", "B", CsTeam.Terrorist, false),
            ("Split B", "B", CsTeam.Terrorist, false),
            ("Split A", "A", CsTeam.Terrorist, false),
            ("Default Controle de Mapa", "Mid", CsTeam.Terrorist, false)
        };

        var roles = new[] { BotRole.AWPer, BotRole.EntryFragger, BotRole.Rotator, BotRole.Anchor };

        foreach (var (tacticName, bombsite, team, isFake) in tacticsToTest)
        {
            var plan = iglService.GenerateDeterministicFallbackPlan(team, BuyState.FULL_BUY, mapProfileManager, "STARTUP_AUDIT");
            foreach (var role in roles)
            {
                string key = RoleManager.GetOrderKey(role);
                if (plan.BotOrders.TryGetValue(key, out var order))
                {
                    audit.PresetsTotal++;
                    bool isC4 = (team == CsTeam.Terrorist && role == BotRole.Rotator);
                    var outcome = ValidateOrder(order, role, tacticName, bombsite, team, isC4, allowCrossSiteLurk: false, isFakeTactic: isFake, mapProfileManager);
                    if (outcome.Result == PresetValidationResult.Valid)
                    {
                        audit.PresetsValid++;
                    }
                    else
                    {
                        audit.PresetsInvalid++;
                        if (outcome.InvalidField == "StagingSpotId" || outcome.InvalidField == "ExecuteSpotId")
                        {
                            audit.MissingSpots++;
                        }
                        if (outcome.InvalidField.Contains("Bombsite") || outcome.InvalidField.Contains("Lurker") || outcome.InvalidField.Contains("C4Carrier"))
                        {
                            audit.IncompatibleBombsites++;
                        }

                        var fallbackOutcome = ValidateAndApplyFallback(order, role, tacticName, bombsite, team, isC4, allowCrossSiteLurk: false, isFakeTactic: isFake, mapProfileManager);
                        if (fallbackOutcome.Result == PresetValidationResult.FallbackSubstituted)
                        {
                            audit.PresetsCorrected++;
                        }
                        audit.AuditMessages.Add($"[{tacticName} - {role}] {outcome.Details} -> {fallbackOutcome.Details}");
                    }
                }
            }
        }

        return audit;
    }
}
