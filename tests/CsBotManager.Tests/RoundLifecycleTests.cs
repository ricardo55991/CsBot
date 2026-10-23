using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class RoundLifecycleTests
{
    [Fact]
    public void Warmup_IsNotCountedAsOfficialRound_AndFirstLiveRoundStartsAtOne()
    {
        var mgr = new RoundLifecycleManager();
        int ctScore = 0, trScore = 0;

        bool startedWarmup = mgr.TryBeginRound(isWarmup: true, gameTick: 100, currentCtScore: ctScore, currentTrScore: trScore, out var warmupRecord, out _);
        Assert.True(startedWarmup);
        Assert.Equal(1, warmupRecord.InternalRoundId);
        Assert.Equal(0, warmupRecord.OfficialRoundNumber);
        Assert.Equal(MatchLifecyclePhase.WARMUP, warmupRecord.MatchPhase);

        // Quando o warmup termina e começa o round oficial 0x0, warmup anterior é auto-selado e OfficialRoundNumber = 1
        bool startedLive = mgr.TryBeginRound(isWarmup: false, gameTick: 500, currentCtScore: ctScore, currentTrScore: trScore, out var liveR1, out var autoSealed);
        Assert.True(startedLive);
        Assert.NotNull(autoSealed);
        Assert.True(autoSealed!.Sealed);
        Assert.Equal("GameCommencing", autoSealed.EndReasonEnum);

        Assert.Equal(2, liveR1.InternalRoundId);
        Assert.Equal(1, liveR1.OfficialRoundNumber);
        Assert.Equal(1, liveR1.RoundNumberInHalf);
        Assert.Equal(MatchLifecyclePhase.LIVE, liveR1.MatchPhase);
        Assert.Equal(RoundLifecyclePhase.FREEZE_TIME, liveR1.RoundPhase);
    }

    [Fact]
    public void DuplicateRoundStart_And_DuplicateRoundEnd_AreIdempotent()
    {
        var mgr = new RoundLifecycleManager();
        int ctScore = 0, trScore = 0, ctLoss = 1, trLoss = 1;

        Assert.True(mgr.TryBeginRound(isWarmup: false, gameTick: 1000, currentCtScore: ctScore, currentTrScore: trScore, out var r1, out _));
        // Callback duplicado no mesmo tick ou +1 tick não pode incrementar round
        Assert.False(mgr.TryBeginRound(isWarmup: false, gameTick: 1001, currentCtScore: ctScore, currentTrScore: trScore, out var rDup, out _));
        Assert.Equal(r1.InternalRoundId, rDup.InternalRoundId);
        Assert.Equal(1, rDup.OfficialRoundNumber);

        Assert.True(mgr.TryTransitionToActivePhase(1900));

        // Primeiro RoundEnd sela o round e atualiza placar
        Assert.True(mgr.TrySealRound(8, CsTeam.CounterTerrorist, 3500, ref ctScore, ref trScore, ref ctLoss, ref trLoss, out var sealed1));
        Assert.NotNull(sealed1);
        Assert.True(sealed1!.Sealed);
        Assert.Equal(1, ctScore);
        Assert.Equal(0, trScore);
        Assert.Equal("CTsWin", sealed1.EndReasonEnum);

        // Segundo RoundEnd duplicado é rejeitado e não altera o placar novamente
        Assert.False(mgr.TrySealRound(8, CsTeam.CounterTerrorist, 3505, ref ctScore, ref trScore, ref ctLoss, ref trLoss, out _));
        Assert.Equal(1, ctScore);
    }

    [Fact]
    public void EventsAfterRoundSeal_And_OlderRoundCallbacks_AreMarkedAsLateEvents()
    {
        var mgr = new RoundLifecycleManager();
        int ctScore = 0, trScore = 0, ctLoss = 1, trLoss = 1;

        mgr.TryBeginRound(isWarmup: false, gameTick: 100, currentCtScore: ctScore, currentTrScore: trScore, out var r1, out _);
        mgr.TryTransitionToActivePhase(200);

        var normalEnv = mgr.CreateEventEnvelope(250, "01:40", "MicroMoveEngine");
        Assert.False(normalEnv.LateEvent);
        Assert.Equal("NORMAL", normalEnv.Disposition);
        Assert.Equal(r1.InternalRoundId, normalEnv.RoundId);

        // Sela o round
        mgr.TrySealRound(12, CsTeam.CounterTerrorist, 500, ref ctScore, ref trScore, ref ctLoss, ref trLoss, out _);

        // Evento emitido após o selamento durante mp_round_restart_delay
        var afterSealEnv = mgr.CreateEventEnvelope(520, "00:00", "MicroMoveEngine");
        Assert.True(afterSealEnv.LateEvent);
        Assert.Equal(LateEventReason.TICK_AFTER_SEAL, afterSealEnv.LateReason);
        Assert.Equal("AUDITED_LATE", afterSealEnv.Disposition);

        // Inicia Round 2 e chega callback assíncrono atrasado do Round 1
        mgr.TryBeginRound(isWarmup: false, gameTick: 900, currentCtScore: ctScore, currentTrScore: trScore, out var r2, out _);
        var asyncLateEnv = mgr.CreateEventEnvelope(910, "01:55", "OllamaIglService", originatingRoundId: r1.InternalRoundId, originatingGameTick: 120, suggestedLateReason: LateEventReason.ASYNC_COMPLETION);
        Assert.True(asyncLateEnv.LateEvent);
        Assert.Equal(LateEventReason.ASYNC_COMPLETION, asyncLateEnv.LateReason);
        Assert.Equal(r1.InternalRoundId, asyncLateEnv.RoundId);
        Assert.Equal(r2.InternalRoundId, asyncLateEnv.CurrentActiveRoundId);
        Assert.Equal(2, mgr.LateEventCount);
    }

    [Fact]
    public void Shutdown_And_MapChange_SealActiveRoundCleanly()
    {
        var mgr = new RoundLifecycleManager();
        mgr.TryBeginRound(isWarmup: false, gameTick: 100, currentCtScore: 1, currentTrScore: 1, out var r, out _);
        mgr.TryTransitionToActivePhase(200);
        Assert.True(mgr.IsMovementAllowed);

        mgr.NotifyPluginShutdown(350);
        Assert.False(mgr.IsMovementAllowed);
        Assert.True(r.Sealed);
        Assert.Equal(MatchLifecyclePhase.PLUGIN_SHUTDOWN, mgr.CurrentMatchPhase);

        mgr.ResetForMapChange(400);
        Assert.Equal(MatchLifecyclePhase.MAP_CHANGE, mgr.CurrentMatchPhase);
    }

    [Fact]
    public void TranslateRoundEndReason_MapsKnownCodes_And_HandlesUnknownCodeWithoutInventingMeaning()
    {
        var r8 = RoundLifecycleManager.TranslateRoundEndReason(8);
        Assert.Equal(8, r8.Code);
        Assert.Equal("CTsWin", r8.EnumName);

        var r12 = RoundLifecycleManager.TranslateRoundEndReason(12);
        Assert.Equal(12, r12.Code);
        Assert.Equal("TargetSaved", r12.EnumName);

        var unknown = RoundLifecycleManager.TranslateRoundEndReason(999);
        Assert.Equal(999, unknown.Code);
        Assert.Equal("UNKNOWN_999", unknown.EnumName);
        Assert.Contains("UNKNOWN_999", unknown.Description);
    }

    [Fact]
    public void BotSystemConfig_DefaultValidation_Succeeds()
    {
        var cfg = BotSystemConfig.Default;
        Assert.True(cfg.Validate(out var errors));
        Assert.Empty(errors);
        Assert.Contains("BotSystemConfig V4", cfg.FormatMarkdownSummary());
    }
}
