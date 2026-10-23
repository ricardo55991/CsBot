using Xunit;

namespace CsBotManager.Tests;

public class GeographyAndPivotTests
{
    [Fact]
    public void MirageSectorClassifier_ClassifiesInteriorBoundaryVerticalOverlapAndNeverReturnsGenericFallback()
    {
        // 1. Pontos interiores reais de cada setor principal
        Assert.Equal("Bomb A", MirageSectorClassifier.Classify(-595f, -2256f, -168f).SectorName);
        Assert.Equal("Bomb B", MirageSectorClassifier.Classify(-1850f, 350f, -160f).SectorName);
        Assert.Equal("Palácio A", MirageSectorClassifier.Classify(-350f, -480f, -90f).SectorName);
        Assert.Equal("Rampa A", MirageSectorClassifier.Classify(-250f, -200f, -160f).SectorName);
        Assert.Equal("Janela", MirageSectorClassifier.Classify(-1380f, -540f, -120f).SectorName);
        Assert.Equal("Conector", MirageSectorClassifier.Classify(-820f, -840f, -160f).SectorName);
        Assert.Equal("Top Mid", MirageSectorClassifier.Classify(450f, -950f, -160f).SectorName);
        Assert.Equal("Apartamentos B", MirageSectorClassifier.Classify(350f, -1350f, -60f).SectorName);
        Assert.Equal("Mercado / Kitchen", MirageSectorClassifier.Classify(-1880f, 180f, -130f).SectorName);
        Assert.Equal("CT Spawn", MirageSectorClassifier.Classify(-1600f, -1950f, -200f).SectorName);
        Assert.Equal("TR Spawn", MirageSectorClassifier.Classify(1200f, -200f, -160f).SectorName);

        // 2. Desempate vertical Z (Underpass Z = -220 vs Catwalk/Short Z = -140 na mesma projeção XY)
        var underpass = MirageSectorClassifier.Classify(-850f, -980f, -230f);
        var catwalkAbove = MirageSectorClassifier.Classify(-850f, -980f, -140f);
        Assert.Equal("Underpass", underpass.SectorName);
        Assert.NotEqual("Underpass", catwalkAbove.SectorName);

        // 3. Mapeamento nativo LastPlaceName da Source 2
        var fromNative = MirageSectorClassifier.Classify(-3000f, -3000f, -160f, nativeLastPlaceName: "TicketBooth");
        Assert.Equal("Ticket / CT", fromNative.SectorName);

        // 4. Nenhum ponto da grade de Mirage pode retornar "Em Trânsito" ou "o Meio"
        for (float x = -2500f; x <= 1400f; x += 350f)
        {
            for (float y = -2400f; y <= 800f; y += 350f)
            {
                var res = MirageSectorClassifier.Classify(x, y, -160f);
                Assert.False(string.IsNullOrWhiteSpace(res.SectorName));
                Assert.NotEqual("Em Trânsito", res.SectorName);
                Assert.NotEqual("o Meio", res.SectorName);
            }
        }
    }

    [Fact]
    public void EvaluateSiteClearance_RejectsBotOutsidePlantPerimeterOrWithInsufficientDwellOrEnemies()
    {
        var config = BotSystemConfig.Default;

        // 1. Bot em Ticket / CT (-1930, -680, -160) tentando declarar Bomb A limpo -> REJEITADO!
        var outsidePerimeter = TrMacroPivotController.EvaluateSiteClearance(
            botX: -1930f, botY: -680f, botZ: -160f,
            nativeLastPlaceName: "TicketBooth",
            inBombZoneFlag: false,
            claimedBombSite: "A",
            dwellSeconds: 4.0f,
            timeSinceLastDamageSeconds: 10.0f,
            nearbyEnemiesCount: 0,
            config: config);

        Assert.False(outsidePerimeter.IsCleared);
        Assert.Contains("OUTSIDE_PLANT_PERIMETER", outsidePerimeter.RejectionReason);

        // 2. Bot dentro da zona real de plant do Bomb A (-595, -2256, -168), mas dwell = 0.8s (< 2.0s) -> REJEITADO!
        var shortDwell = TrMacroPivotController.EvaluateSiteClearance(
            botX: -595f, botY: -2256f, botZ: -168f,
            nativeLastPlaceName: "BombsiteA",
            inBombZoneFlag: true,
            claimedBombSite: "A",
            dwellSeconds: 0.8f,
            timeSinceLastDamageSeconds: 10.0f,
            nearbyEnemiesCount: 0,
            config: config);

        Assert.False(shortDwell.IsCleared);
        Assert.Contains("INSUFFICIENT_DWELL_TIME", shortDwell.RejectionReason);

        // 3. Bot dentro da zona real de plant do Bomb A, dwell = 2.8s, sem dano, sem CTs próximos -> APROVADO!
        var validClear = TrMacroPivotController.EvaluateSiteClearance(
            botX: -595f, botY: -2256f, botZ: -168f,
            nativeLastPlaceName: "BombsiteA",
            inBombZoneFlag: true,
            claimedBombSite: "A",
            dwellSeconds: 2.8f,
            timeSinceLastDamageSeconds: 6.0f,
            nearbyEnemiesCount: 0,
            config: config);

        Assert.True(validClear.IsCleared);
        Assert.Equal("NONE", validClear.RejectionReason);
        Assert.True(validClear.Confidence >= config.BombsiteClearMinConfidence);
    }

    [Fact]
    public void ResolveFirstKillExploitContext_UsesRealSectorsAndIncrementsTacticRevision()
    {
        // First kill obtido nos Apartamentos B com a C4 próxima do Bomb B -> deve selecionar Bomb B e setor real "Apartamentos B"
        var ctx = TrMacroPivotController.ResolveFirstKillExploitContext(
            killerName: "Ricksaw",
            killerX: 50f, killerY: -1300f, killerZ: -60f, killerNativePlace: "Apartments",
            victimName: "Phoenix",
            victimX: -1280f, victimY: -120f, victimZ: -140f, victimNativePlace: "Truck",
            bombCarrierName: "Delrow",
            c4X: 150f, c4Y: -1300f, c4Z: -60f, c4NativePlace: "Apartments",
            aliveTrCount: 5,
            aliveCtCount: 4,
            roundTimeRemaining: 88.0f,
            currentTargetSite: "A");

        Assert.Equal("Apartamentos B", ctx.KillerSector);
        Assert.Equal("Van", ctx.VictimSector);
        Assert.Equal("B", ctx.SelectedTargetSite);
        Assert.DoesNotContain("o Meio", ctx.SelectedTacticName);

        var plan = new TacticalPlan();
        plan.InitializeVersioning("Slow Default TR", "A", TacticalDecisionSource.OLLAMA, tick: 100);
        Assert.Equal(1, plan.TacticRevision);

        plan.ApplyPivotRevision(
            ctx.SelectedTacticName,
            ctx.SelectedTargetSite,
            "First kill in Van",
            "FirstKillMidRoundExploit",
            gameTick: 500,
            roundTime: "01:28",
            confidence: ctx.Confidence);

        Assert.Equal(2, plan.TacticRevision);
        Assert.Equal("Slow Default TR", plan.InitialTactic);
        Assert.Equal(ctx.SelectedTacticName, plan.CurrentTactic);
        Assert.Equal("A", plan.PreviousTargetSite);
        Assert.Equal("B", plan.CurrentTargetSite);
    }
}
