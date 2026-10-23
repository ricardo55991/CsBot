using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class TelemetryAndDamageTests
{
    private static (Dictionary<int, int> hp, HashSet<(int, int, int, string)> dedup) NewState() => (new(), new());

    [Fact]
    public void AppliedDamage_IsHpDelta_NotRawDamage()
    {
        var (hp, dd) = NewState();
        var d = MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 143, 0);
        Assert.Equal(100, d.HpBefore);
        Assert.Equal(100, d.AppliedDamage);
        Assert.Equal(43, d.OverkillDamage);
        Assert.Null(d.ZeroDamageReason);
    }

    [Fact]
    public void SequentialHits_UseLastKnownHealth()
    {
        var (hp, dd) = NewState();
        MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 27, 73);
        var d = MatchTelemetryLogger.ComputeDamage(hp, dd, 110, 1, 2, "ak47", 27, 46);
        Assert.Equal(73, d.HpBefore);
        Assert.Equal(27, d.AppliedDamage);
    }

    [Fact]
    public void DuplicateEventSameTick_IsDiscarded()
    {
        var (hp, dd) = NewState();
        MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 27, 73);
        var d = MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 27, 73);
        Assert.True(d.IsDuplicate);
    }

    [Fact]
    public void ZeroDamage_HasExplicitReason()
    {
        var (hp, dd) = NewState();
        MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 150, 0);
        var dead = MatchTelemetryLogger.ComputeDamage(hp, dd, 101, 3, 2, "m4a1", 30, 0);
        Assert.Equal(0, dead.AppliedDamage);
        Assert.Equal("VICTIM_ALREADY_DEAD", dead.ZeroDamageReason);

        var (hp2, dd2) = NewState();
        var armor = MatchTelemetryLogger.ComputeDamage(hp2, dd2, 100, 1, 5, "hegrenade", 0, 100, armorDamage: 5);
        Assert.Equal("ABSORBED_BY_ARMOR", armor.ZeroDamageReason);
    }

    [Fact]
    public void OutOfOrderCallback_NeverProducesNegativeDamage()
    {
        var (hp, dd) = NewState();
        hp[2] = 40;
        var d = MatchTelemetryLogger.ComputeDamage(hp, dd, 100, 1, 2, "ak47", 10, 90);
        Assert.True(d.AppliedDamage >= 0);
    }

    [Fact]
    public void Velocity2D_IgnoresVerticalComponent()
    {
        var (v2, vz, v3) = MatchTelemetryLogger.ComputeVelocity(150f, 200f, -300f);
        Assert.Equal(250f, v2, 3);
        Assert.Equal(-300f, vz);
        Assert.True(v3 > 390f);
    }

    [Fact]
    public void LateEvent_AfterSeal_IsFlagged()
    {
        var lc = new RoundLifecycleManager();
        lc.TryBeginRound(false, 10, 0, 0, out _, out _);
        lc.TryTransitionToActivePhase(20);
        int ct = 0, tr = 0, cl = 1, tl = 1;
        Assert.True(lc.TrySealRound(8, CounterStrikeSharp.API.Modules.Utils.CsTeam.CounterTerrorist, 500, ref ct, ref tr, ref cl, ref tl, out _));
        Assert.False(lc.TrySealRound(8, CounterStrikeSharp.API.Modules.Utils.CsTeam.CounterTerrorist, 501, ref ct, ref tr, ref cl, ref tl, out _));
        Assert.Equal(1, ct);
        var env = lc.CreateEventEnvelope(510, "00:00", "EventPlayerDeath");
        Assert.True(env.LateEvent);
        Assert.Equal("AUDITED_LATE", env.Disposition);
    }
}
