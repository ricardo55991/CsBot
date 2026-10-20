using CounterStrikeSharp.API.Core;

namespace CsBotManager;

public class TacticalHudRenderer
{
    public static string BuildChipHudHtml(
        BuyState buyState,
        TacticalPlan plan,
        RoleManager roleManager,
        MapProfileManager mapProfileManager,
        PacingAndFallbackController pacingController,
        List<CCSPlayerController> teamBots,
        VoiceCommandBridge? voiceBridge = null)
    {
        string stateColor = buyState switch
        {
            BuyState.FULL_BUY => "#00FF66",
            BuyState.FORCE_BUY => "#FFA500",
            BuyState.HALF_BUY => "#FFD700",
            BuyState.FULL_ECO => "#FF3344",
            _ => "#FFFFFF"
        };

        string stateName = buyState switch
        {
            BuyState.FULL_BUY => "FULL BUY",
            BuyState.FORCE_BUY => "FORCE BUY",
            BuyState.HALF_BUY => "HALF BUY",
            BuyState.FULL_ECO => "FULL ECO",
            _ => buyState.ToString()
        };

        (string tempoName, string tempoColor) = plan.RoundTempo switch
        {
            RoundTempo.SLOW_DEFAULT => ("LENTO DEFAULT", "#00FFCC"),
            RoundTempo.POKE_AND_ROTATE => ("TESTE & ROTAÇÃO", "#FFD700"),
            RoundTempo.TIMED_EXECUTE => ("EXEC SINCRONIZADA", "#FFA500"),
            RoundTempo.FAST_CONTACT => ("CONTATO RÁPIDO", "#FF3344"),
            _ => ("PADRÃO", "#FFFFFF")
        };

        string phaseBadge = plan.CurrentPhase switch
        {
            RoundPhase.FreezeTime => "<font color='#AAAAAA'>[CONGELAMENTO]</font>",
            RoundPhase.Staging => $"<font color='#00E5FF'>[STAGING: {pacingController.StagingTimeRemaining:F0}s]</font>",
            RoundPhase.Executing => "<font color='#FF5555'>[EXECUTE ATIVO]</font>",
            RoundPhase.PostPlant => "<font color='#FFFF00'>[PÓS-PLANT]</font>",
            _ => ""
        };

        string tierBadge = plan.PlayTier switch
        {
            PlayTier.Tier1_Standard => "<font color='#00FF88'>[TIER 1]</font>",
            PlayTier.Tier2_Moderate => "<font color='#00E5FF'>[TIER 2]</font>",
            PlayTier.Tier3_Cheese => "<font color='#FF0055'>[TIER 3: CHEESE]</font>",
            _ => ""
        };

        string clockBadge = "";
        if (plan.IsTacticalSaveActive)
        {
            clockBadge = " <font color='#FFAA00'><b>[SAVE TÁTICO]</b></font>";
        }
        else if (plan.IsHeroicAttempt)
        {
            clockBadge = " <font color='#FF00FF'><b>[CLUTCH HEROICO 5%]</b></font>";
        }
        else if (plan.IsClockDesperationActive)
        {
            clockBadge = " <font color='#FF2222'><b>[DESESPERO &lt;22s]</b></font>";
        }
        else if (plan.IsLateRoundSilenceActive)
        {
            clockBadge = " <font color='#9999FF'><b>[SILÊNCIO]</b></font>";
        }

        string tacticalBadge = "";
        if (plan.IsFlankCoverActive)
        {
            tacticalBadge = " <font color='#00E5FF'>[ANTI-RUSH ATIVO]</font>";
        }
        else if (plan.CurrentAlertLevel == AlertLevel.Level1_PressureNoBomb)
        {
            tacticalBadge = " <font color='#FFA500'>[ALERTA 1: PRESSÃO]</font>";
        }
        else if (plan.CurrentAlertLevel == AlertLevel.Level2_BombConfirmed)
        {
            tacticalBadge = " <font color='#FF0000'>[ALERTA 2: C4 CONFIRMADA]</font>";
        }
        else if (plan.CtDuoPlay != CtDuoPlayType.None)
        {
            tacticalBadge = $" <font color='#00FF88'>[DUO: {plan.CtDuoPlay}]</font>";
        }
        else if (plan.TrTacticType == TrTacticType.SPLIT_FAKE)
        {
            tacticalBadge = " <font color='#FFCC00'>[SPLIT FAKE]</font>";
        }

        var botParts = new List<string>();
        foreach (var bot in teamBots)
        {
            var role = roleManager.GetBotRole(bot);
            if (role != null)
            {
                string key = RoleManager.GetOrderKey(role.Value);
                if (plan.BotOrders.TryGetValue(key, out var order))
                {
                    string shortRole = role.Value switch
                    {
                        BotRole.AWPer => "AWP",
                        BotRole.EntryFragger => "Entry",
                        BotRole.Rotator => "Rot",
                        BotRole.Anchor => "Anc",
                        _ => "Bot"
                    };

                    string activeSpotId = (plan.CurrentPhase == RoundPhase.Executing)
                        ? order.ExecuteSpotId
                        : order.StagingSpotId;

                    var spot = mapProfileManager.GetSpotById(activeSpotId);
                    string spotName = spot?.Name ?? order.TargetArea;

                    string stanceBadge = order.IsFallingBack ? "Recuando" : order.HoldSiteLocked ? "Travado B" : order.Stance switch
                    {
                        EngagementStance.PASSIVE_HOLD => "Passivo",
                        EngagementStance.JIGGLE_INFO => "Jiggle",
                        EngagementStance.ONE_AND_DONE => "One&Done",
                        EngagementStance.AGGRESSIVE_POKE => "Poke",
                        _ => "Hold"
                    };

                    botParts.Add($"<b>{shortRole}:</b> {spotName} <font color='#88FF88'>({stanceBadge})</font>");
                }
            }
        }

        string botSummary = botParts.Count > 0 ? string.Join(" | ", botParts) : "Bots alinhados na tática";

        string voiceHeader = "";
        if (voiceBridge != null && !string.IsNullOrEmpty(voiceBridge.LastVoiceCommand))
        {
            string sanitizedVoiceCmd = System.Net.WebUtility.HtmlEncode(voiceBridge.LastVoiceCommand);
            voiceHeader = $"<font color='#00FFCC' size='2'>🎙️ <i>\"{sanitizedVoiceCmd}\"</i></font><br>";
        }

        string sanitizedTacticName = System.Net.WebUtility.HtmlEncode(plan.TacticName ?? "");
        string sanitizedTacticSummary = System.Net.WebUtility.HtmlEncode(plan.TacticSummary ?? "");

        return $@"
{voiceHeader}<font color='{stateColor}' size='3'><b>[{stateName}]</b></font> {tierBadge} <font color='{tempoColor}' size='3'><b>[{tempoName}]</b></font> {phaseBadge}{tacticalBadge}{clockBadge} <font color='#00E5FF' size='3'><b>⚡ {sanitizedTacticName}</b></font><br>
<font color='#FFFFFF' size='2'>{sanitizedTacticSummary}</font><br>
<font color='#DDDDDD' size='2'>{botSummary}</font><br>
<font color='#888888' size='1'><i>[!executar / !go | !tatica &lt;call&gt; | !pos &lt;setor&gt; | !flash &lt;setor&gt; | PTT: Segure V]</i></font>
";
    }

    public static void RenderChipHud(
        CCSPlayerController player,
        BuyState buyState,
        TacticalPlan plan,
        RoleManager roleManager,
        MapProfileManager mapProfileManager,
        PacingAndFallbackController pacingController,
        List<CCSPlayerController> teamBots,
        VoiceCommandBridge? voiceBridge = null)
    {
        if (!player.IsValid || player.IsBot) return;
        string html = BuildChipHudHtml(buyState, plan, roleManager, mapProfileManager, pacingController, teamBots, voiceBridge);
        player.PrintToCenterHtml(html);
    }
}
