using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

/// <summary>
/// Catálogo tático homologado de de_mirage (7 formações CT e 7 táticas TR com SpotIds validados de de_mirage.json).
/// </summary>
public sealed class MirageTacticalCatalog : IMapTacticalCatalog
{
    public string MapName => "de_mirage";
    public IReadOnlyList<CtTacticBlueprint> CtTactics { get; }
    public IReadOnlyList<TrTacticBlueprint> TrTactics { get; }

    public MirageTacticalCatalog()
    {
        CtTactics = BuildCtCatalog();
        TrTactics = BuildTrCatalog();
    }

    public bool TryRouteMapSpecificLexicalCall(CsTeam team, string text, out string matchedTacticId, out string matchedReason)
    {
        matchedTacticId = string.Empty;
        matchedReason = string.Empty;

        if (team == CsTeam.Terrorist)
        {
            if (ContainsAny(text, "fake a", "finge a", "barulho a", "enganar a"))
            {
                matchedTacticId = "TR_FAKE_A_EXEC_B";
                matchedReason = "MirageLexical:FakeA_ExecB";
                return true;
            }
            if (ContainsAny(text, "fake b", "finge b", "barulho b", "enganar b"))
            {
                matchedTacticId = "TR_FAKE_B_EXEC_A";
                matchedReason = "MirageLexical:FakeB_ExecA";
                return true;
            }
            if (ContainsAny(text, "split b", "meio pro b", "l pro b", "catwalk b"))
            {
                matchedTacticId = "TR_SPLIT_B_MID_TO_SHORT_CATWALK";
                matchedReason = "MirageLexical:SplitB";
                return true;
            }
            if (ContainsAny(text, "split a", "meio pro a", "liga pro a", "conector a"))
            {
                matchedTacticId = "TR_SPLIT_A_MID_TO_CONNECTOR";
                matchedReason = "MirageLexical:SplitA";
                return true;
            }
            if (ContainsAny(text, "rush b", "exec b", "bora b", "entra b", "tapete", "apartamento"))
            {
                matchedTacticId = "TR_EXEC_B_APARTMENTS_RUSH";
                matchedReason = "MirageLexical:ExecRushB";
                return true;
            }
            if (ContainsAny(text, "rush a", "exec a", "bora a", "entra a", "palacio", "palácio", "rampa a"))
            {
                matchedTacticId = "TR_EXEC_A_PALACE_RAMP_SPLIT";
                matchedReason = "MirageLexical:ExecA";
                return true;
            }
            if (ContainsAny(text, "default", "padrao", "padrão", "lento", "controle", "calma", "espera"))
            {
                matchedTacticId = "TR_SLOW_DEFAULT_MAP_CONTROL";
                matchedReason = "MirageLexical:SlowDefault";
                return true;
            }
        }
        else if (team == CsTeam.CounterTerrorist)
        {
            if (ContainsAny(text, "stack a", "gamble a", "todos no a", "fecha a"))
            {
                matchedTacticId = "CT_ECO_STACK_GAMBLE_A";
                matchedReason = "MirageLexical:StackA";
                return true;
            }
            if (ContainsAny(text, "stack b", "gamble b", "todos no b", "fecha b"))
            {
                matchedTacticId = "CT_ECO_STACK_GAMBLE_B";
                matchedReason = "MirageLexical:StackB";
                return true;
            }
            if (ContainsAny(text, "meio agressivo", "domina meio", "dominio meio", "avança meio", "avanca meio", "3 meio"))
            {
                matchedTacticId = "CT_MID_AGGRESSIVE_DOMINANCE";
                matchedReason = "MirageLexical:MidDominance";
                return true;
            }
            if (ContainsAny(text, "reforça b", "reforca b", "pesado b", "anchor b", "anti rush b", "segura b"))
            {
                matchedTacticId = "CT_2_1_2_HEAVY_ANCHOR_B";
                matchedReason = "MirageLexical:HeavyB";
                return true;
            }
            if (ContainsAny(text, "reforça a", "reforca a", "pesado a", "caverna", "palacio", "palácio", "segura a"))
            {
                matchedTacticId = "CT_2_1_2_HEAVY_PALACE_RAMP_A";
                matchedReason = "MirageLexical:HeavyA";
                return true;
            }
            if (ContainsAny(text, "retake", "passivo", "recuado", "guarda util", "joga pelo retake"))
            {
                matchedTacticId = "CT_RETAKE_PASSIVE_SETUP";
                matchedReason = "MirageLexical:RetakeSetup";
                return true;
            }
            if (ContainsAny(text, "2-1-2", "212", "padrao", "padrão", "equilibrado", "default"))
            {
                matchedTacticId = "CT_STANDARD_2_1_2_BALANCED";
                matchedReason = "MirageLexical:Standard212";
                return true;
            }
        }

        return false;
    }

    private static bool ContainsAny(string input, params string[] keywords)
    {
        foreach (var kw in keywords)
        {
            if (input.Contains(kw, StringComparison.OrdinalIgnoreCase))
                return true;
        }
        return false;
    }

    private static List<CtTacticBlueprint> BuildCtCatalog()
    {
        return new List<CtTacticBlueprint>
        {
            // 1. CT_STANDARD_2_1_2_BALANCED
            new CtTacticBlueprint
            {
                TacticId = "CT_STANDARD_2_1_2_BALANCED",
                TacticName = "Defesa 2-1-2 Padrão Equilibrada",
                TacticSummary = "2 A (Ticket + Cabecinha), 1 Meio (Janela), 2 B (Van + Banco) com AuthorizedHold.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                StagingDuration = 22.0f,
                FocusSector = "BALANCED",
                PrefersAwp = true,
                IsAntiEcoFriendly = true,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "Mid", InitialSpot = "ct_mid_window_deep_awp", ExecuteSpot = "ct_mid_window_crouch", HoldMinimumDuration = 25f, RotationTrigger = "C4_SIGHTED_OR_SITE_LOST" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ticket_passive", ExecuteSpot = "ct_a_ticket_passive", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "A", InitialSpot = "ct_a_stairs_cross", ExecuteSpot = "ct_a_jungle_support", HoldMinimumDuration = 20f, RotationTrigger = "B_HEAVY_EXEC_CONFIRMED" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_bench_deep", ExecuteSpot = "ct_b_site_default_crouch", HoldMinimumDuration = 35f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "B", InitialSpot = "ct_b_van_peek", ExecuteSpot = "ct_b_short_corner", HoldMinimumDuration = 22f, RotationTrigger = "A_HEAVY_EXEC_CONFIRMED" }
                }
            },

            // 2. CT_2_1_2_HEAVY_ANCHOR_B
            new CtTacticBlueprint
            {
                TacticId = "CT_2_1_2_HEAVY_ANCHOR_B",
                TacticName = "Defesa 2-1-2 Anti-Rush B (Tapete + Short)",
                TacticSummary = "Crossfire pesado no Bomb B (Pilar + Short + Mercado/Van) para travar execuções no Tapete.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                StagingDuration = 24.0f,
                FocusSector = "B",
                PrefersAwp = false,
                IsAntiEcoFriendly = true,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "Mid", InitialSpot = "ct_mid_window_crouch", ExecuteSpot = "ct_mid_short_catwalk", HoldMinimumDuration = 22f, RotationTrigger = "B_APARTMENTS_CONTACT" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ticket_passive", ExecuteSpot = "ct_a_triple_jiggle", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "A", InitialSpot = "ct_a_jungle_support", ExecuteSpot = "ct_a_stairs_cross", HoldMinimumDuration = 18f, RotationTrigger = "B_HEAVY_CONTACT" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_site_default_crouch", ExecuteSpot = "ct_b_bench_deep", HoldMinimumDuration = 35f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "B", InitialSpot = "ct_b_short_corner", ExecuteSpot = "ct_b_market_window", HoldMinimumDuration = 28f, RotationTrigger = "A_SITE_TAKEN" }
                }
            },

            // 3. CT_2_1_2_HEAVY_PALACE_RAMP_A
            new CtTacticBlueprint
            {
                TacticId = "CT_2_1_2_HEAVY_PALACE_RAMP_A",
                TacticName = "Defesa 2-1-2 Crossfire Pesado Bomb A",
                TacticSummary = "Foco em travar Rampa e Palácio A com Firebox, Cabecinha e Conector.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                StagingDuration = 24.0f,
                DuoPlay = CtDuoPlayType.DominioCavernaRamp,
                FocusSector = "A",
                PrefersAwp = true,
                IsAntiEcoFriendly = true,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "Mid", InitialSpot = "ct_mid_connector_headshot", ExecuteSpot = "ct_a_jungle_support", HoldMinimumDuration = 22f, RotationTrigger = "A_RAMP_CONTACT" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_firebox_oneanddone", ExecuteSpot = "ct_a_ticket_passive", HoldMinimumDuration = 32f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "A", InitialSpot = "ct_a_stairs_cross", ExecuteSpot = "ct_a_palace_close_poke", HoldMinimumDuration = 25f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_van_peek", ExecuteSpot = "ct_b_bench_deep", HoldMinimumDuration = 32f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "B", InitialSpot = "ct_b_market_window", ExecuteSpot = "ct_b_short_corner", HoldMinimumDuration = 18f, RotationTrigger = "A_HEAVY_EXEC_CONFIRMED" }
                }
            },

            // 4. CT_MID_AGGRESSIVE_DOMINANCE
            new CtTacticBlueprint
            {
                TacticId = "CT_MID_AGGRESSIVE_DOMINANCE",
                TacticName = "Domínio Agressivo de Meio (1-3-1)",
                TacticSummary = "1 Âncora A, 3 dominando Meio (Janela + Conector + L/Short) e 1 Âncora B.",
                Tempo = RoundTempo.POKE_AND_ROTATE,
                StagingDuration = 18.0f,
                DuoPlay = CtDuoPlayType.DominioMeio,
                FocusSector = "MID",
                PrefersAwp = true,
                IsAntiEcoFriendly = false,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "Mid", InitialSpot = "ct_mid_window_deep_awp", ExecuteSpot = "ct_mid_window_crouch", HoldMinimumDuration = 20f, RotationTrigger = "SITE_EXEC_CONFIRMED" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ticket_passive", ExecuteSpot = "ct_a_triple_jiggle", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "Mid", InitialSpot = "ct_mid_connector_headshot", ExecuteSpot = "ct_a_stairs_cross", HoldMinimumDuration = 18f, RotationTrigger = "A_PRESSURE" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_bench_deep", ExecuteSpot = "ct_b_site_default_crouch", HoldMinimumDuration = 32f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "Mid", InitialSpot = "ct_mid_short_catwalk", ExecuteSpot = "ct_b_short_corner", HoldMinimumDuration = 18f, RotationTrigger = "B_PRESSURE" }
                }
            },

            // 5. CT_ECO_STACK_GAMBLE_A
            new CtTacticBlueprint
            {
                TacticId = "CT_ECO_STACK_GAMBLE_A",
                TacticName = "Gamble Eco Stack A (Curta Distância)",
                TacticSummary = "Formação de Eco/Pistola focada em emboscada curta no Bomb A (Ninja, Firebox, Palácio, Cabecinha).",
                Tempo = RoundTempo.FAST_CONTACT,
                StagingDuration = 25.0f,
                FocusSector = "A",
                IsEcoStackGamble = true,
                PrefersAwp = false,
                IsAntiEcoFriendly = false,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ninja_hide", ExecuteSpot = "ct_a_firebox_oneanddone", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "A", InitialSpot = "ct_a_palace_close_poke", ExecuteSpot = "ct_a_stairs_cross", HoldMinimumDuration = 28f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "A", InitialSpot = "ct_a_firebox_oneanddone", ExecuteSpot = "ct_a_triple_jiggle", HoldMinimumDuration = 28f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "Mid", InitialSpot = "ct_mid_connector_headshot", ExecuteSpot = "ct_a_jungle_support", HoldMinimumDuration = 22f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_van_peek", ExecuteSpot = "ct_b_site_default_crouch", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_A" }
                }
            },

            // 6. CT_ECO_STACK_GAMBLE_B
            new CtTacticBlueprint
            {
                TacticId = "CT_ECO_STACK_GAMBLE_B",
                TacticName = "Gamble Eco Stack B (Emboscada Tapete)",
                TacticSummary = "Formação de Eco/Pistola com 3 defensores em ângulos curtos no Bomb B + 1 Underpass.",
                Tempo = RoundTempo.FAST_CONTACT,
                StagingDuration = 25.0f,
                FocusSector = "B",
                IsEcoStackGamble = true,
                PrefersAwp = false,
                IsAntiEcoFriendly = false,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_van_peek", ExecuteSpot = "ct_b_bench_deep", HoldMinimumDuration = 32f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "B", InitialSpot = "ct_b_site_default_crouch", ExecuteSpot = "ct_b_short_corner", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "B", InitialSpot = "ct_b_short_corner", ExecuteSpot = "ct_b_market_window", HoldMinimumDuration = 28f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "Mid", InitialSpot = "ct_mid_underpass_peek", ExecuteSpot = "ct_mid_short_catwalk", HoldMinimumDuration = 22f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ticket_passive", ExecuteSpot = "ct_a_jungle_support", HoldMinimumDuration = 30f, RotationTrigger = "BOMB_PLANTED_B" }
                }
            },

            // 7. CT_RETAKE_PASSIVE_SETUP
            new CtTacticBlueprint
            {
                TacticId = "CT_RETAKE_PASSIVE_SETUP",
                TacticName = "Setup Passivo de Retake e Preservação de Utilitárias",
                TacticSummary = "Ângulos profundos de sobrevivência (Ticket, Jungle, Janela, Mercado, Banco) para jogar pelo Retake 5v5.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                StagingDuration = 26.0f,
                FocusSector = "RETAKE",
                PrefersAwp = true,
                IsAntiEcoFriendly = true,
                Assignments = new List<CtFormationAssignment>
                {
                    new() { FormationRole = CtFormationRole.Mid_Controller, AssignedSite = "Mid", InitialSpot = "ct_mid_window_crouch", ExecuteSpot = "ct_a_jungle_support", HoldMinimumDuration = 25f, RotationTrigger = "SITE_EXEC_CONFIRMED" },
                    new() { FormationRole = CtFormationRole.A1_Anchor, AssignedSite = "A", InitialSpot = "ct_a_ticket_passive", ExecuteSpot = "ct_a_ticket_passive", HoldMinimumDuration = 35f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.A2_Support, AssignedSite = "A", InitialSpot = "ct_a_jungle_support", ExecuteSpot = "ct_a_stairs_cross", HoldMinimumDuration = 25f, RotationTrigger = "BOMB_PLANTED_B" },
                    new() { FormationRole = CtFormationRole.B1_Anchor, AssignedSite = "B", InitialSpot = "ct_b_bench_deep", ExecuteSpot = "ct_b_market_door", HoldMinimumDuration = 35f, RotationTrigger = "BOMB_PLANTED_A" },
                    new() { FormationRole = CtFormationRole.B2_Support, AssignedSite = "B", InitialSpot = "ct_b_market_window", ExecuteSpot = "ct_b_site_default_crouch", HoldMinimumDuration = 28f, RotationTrigger = "BOMB_PLANTED_A" }
                }
            }
        };
    }

    private static List<TrTacticBlueprint> BuildTrCatalog()
    {
        return new List<TrTacticBlueprint>
        {
            // 1. TR_SLOW_DEFAULT_MAP_CONTROL
            new TrTacticBlueprint
            {
                TacticId = "TR_SLOW_DEFAULT_MAP_CONTROL",
                TacticName = "Default Lento de Controle de Mapa (1-2-2)",
                TacticSummary = "1 Top Mid, 2 Rampa/Palácio A, 2 Tapete/Underpass B buscando pick inicial antes de executar A.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                StagingDuration = 18.0f,
                TacticType = TrTacticType.Default,
                TargetSite = "A",
                RealSite = "A",
                IsSlowLongRange = true,
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "AWPer", TargetArea = "Middle", RoleAction = "Hold Top Mid for Window/Connector pick", StagingSpotId = "tr_staging_top_mid_boxes", ExecuteSpotId = "tr_exec_mid_connector_push", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite A", RoleAction = "Probe A Ramp and clear close angles", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_triple_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite A", RoleAction = "Protect C4 at T Roof and plant Default A", StagingSpotId = "tr_staging_t_roof", ExecuteSpotId = "tr_exec_a_site_default", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite A", RoleAction = "Control Palace interior and trade A site", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.JIGGLE_INFO, RequiredUtilities = new() { "smoke", "molotov" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite B", RoleAction = "Lurk Underpass/B Apps to cut CT rotations", StagingSpotId = "tr_staging_underpass_top", ExecuteSpotId = "tr_exec_mid_connector_push", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "flashbang", "hegrenade" } }
                }
            },

            // 2. TR_EXEC_A_PALACE_RAMP_SPLIT
            new TrTacticBlueprint
            {
                TacticId = "TR_EXEC_A_PALACE_RAMP_SPLIT",
                TacticName = "Execução Coordenada Bomb A (Rampa + Palácio)",
                TacticSummary = "Smokes Cabecinha/Jungle/CT e entrada simultânea Rampa A + Palácio com plant seguro no Default.",
                Tempo = RoundTempo.TIMED_EXECUTE,
                StagingDuration = 11.0f,
                TacticType = TrTacticType.Default,
                TargetSite = "A",
                RealSite = "A",
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite A", RoleAction = "Entry A Ramp clearing Triple and Firebox", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_triple_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "AWPer", TargetArea = "Bombsite A", RoleAction = "Throw Ramp smoke and hold Ticket/CT cross", StagingSpotId = "tr_staging_t_roof", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite A", RoleAction = "Advance with C4 behind Entry to plant Default A", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_site_default", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite A", RoleAction = "Exit Palace clearing Stairs and Jungle", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite A", RoleAction = "Support Palace/Ramp trade and watch CT flank", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_a_triple_clear", Stance = EngagementStance.JIGGLE_INFO, RequiredUtilities = new() { "smoke", "hegrenade" } }
                }
            },

            // 3. TR_EXEC_B_APARTMENTS_RUSH
            new TrTacticBlueprint
            {
                TacticId = "TR_EXEC_B_APARTMENTS_RUSH",
                TacticName = "Execução Rápida Tapete B (Rush Apartamentos)",
                TacticSummary = "Explosão coordenada pelo Tapete B com limpeza da Van, Banco e contenção da Janela do Mercado.",
                Tempo = RoundTempo.FAST_CONTACT,
                StagingDuration = 6.5f,
                TacticType = TrTacticType.Default,
                TargetSite = "B",
                RealSite = "B",
                IsFastCloseRange = true,
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite B", RoleAction = "Jump out B Balcony and clear Van/Bench", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_van_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite B", RoleAction = "Second entry B clearing Site Pillar and Market Window", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite B", RoleAction = "Escort C4 through Apartments and plant B safe", StagingSpotId = "tr_staging_b_apartments_house", ExecuteSpotId = "tr_exec_b_site_plant", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "AWPer", TargetArea = "Bombsite B", RoleAction = "Hold Short/Catwalk cross from Apartments", StagingSpotId = "tr_staging_b_apartments_house", ExecuteSpotId = "tr_exec_b_van_clear", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "flashbang", "hegrenade" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite B", RoleAction = "Clear Underpass/Apps flank and lock Market door", StagingSpotId = "tr_staging_underpass_top", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.JIGGLE_INFO, RequiredUtilities = new() { "smoke", "molotov" } }
                }
            },

            // 4. TR_SPLIT_A_MID_TO_CONNECTOR
            new TrTacticBlueprint
            {
                TacticId = "TR_SPLIT_A_MID_TO_CONNECTOR",
                TacticName = "Split A pelo Meio e Conector",
                TacticSummary = "Domínio do Meio (Top Mid + Underpass) invadindo Conector/Jungle em pinça com Rampa A.",
                Tempo = RoundTempo.TIMED_EXECUTE,
                StagingDuration = 13.0f,
                TacticType = TrTacticType.Default,
                TargetSite = "A",
                RealSite = "A",
                IsSplitPlay = true,
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "AWPer", TargetArea = "Middle", RoleAction = "Smoke Window and suppress Mid from Top Boxes", StagingSpotId = "tr_staging_top_mid_boxes", ExecuteSpotId = "tr_exec_mid_connector_push", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "EntryFragger", TargetArea = "Middle", RoleAction = "Push Underpass to Connector and clear Stairs/Jungle", StagingSpotId = "tr_staging_underpass_top", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite A", RoleAction = "Carry C4 via A Ramp synchronized with Connector pinch", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_site_default", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite A", RoleAction = "Clear Triple/Ticket from A Ramp", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_triple_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "hegrenade" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite A", RoleAction = "Lurk Palace and pinch Stairs", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.JIGGLE_INFO, RequiredUtilities = new() { "molotov" } }
                }
            },

            // 5. TR_SPLIT_B_MID_TO_SHORT_CATWALK
            new TrTacticBlueprint
            {
                TacticId = "TR_SPLIT_B_MID_TO_SHORT_CATWALK",
                TacticName = "Split B pelo Meio/Catwalk e Tapete",
                TacticSummary = "2 jogadores dominam Meio/Underpass para subir L (Short B) enquanto 3 entram pelo Tapete B com a C4.",
                Tempo = RoundTempo.TIMED_EXECUTE,
                StagingDuration = 12.5f,
                TacticType = TrTacticType.Default,
                TargetSite = "B",
                RealSite = "B",
                IsSplitPlay = true,
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite B", RoleAction = "Break B site from Apartments Kitchen clearing Van", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_van_clear", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite B", RoleAction = "Advance with C4 in B Apartments and plant B Default", StagingSpotId = "tr_staging_b_apartments_house", ExecuteSpotId = "tr_exec_b_site_plant", Stance = EngagementStance.PASSIVE_HOLD, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite B", RoleAction = "Push B Apartments to lock Market Window", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "AWPer", TargetArea = "Middle", RoleAction = "Control Top Mid and pinch B Short/Catwalk", StagingSpotId = "tr_staging_top_mid_boxes", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Middle", RoleAction = "Push Underpass to Catwalk/Short B", StagingSpotId = "tr_staging_underpass_top", ExecuteSpotId = "tr_exec_b_site_plant", Stance = EngagementStance.AGGRESSIVE_POKE, RequiredUtilities = new() { "flashbang", "hegrenade" } }
                }
            },

            // 6. TR_FAKE_A_EXEC_B (Fake em A sem C4; Execução Real em B com C4!)
            new TrTacticBlueprint
            {
                TacticId = "TR_FAKE_A_EXEC_B",
                TacticName = "Fake A & Execução Real Bomb B",
                TacticSummary = "2 jogadores sem C4 gastam utilitárias e fazem barulho na Rampa/Palácio A; Carrier + 2 executam o Bomb B.",
                Tempo = RoundTempo.POKE_AND_ROTATE,
                StagingDuration = 12.0f,
                TacticType = TrTacticType.SPLIT_FAKE,
                TargetSite = "B",
                FakeSite = "A",
                RealSite = "B",
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite B", RoleAction = "Silent staging in B Kitchen then burst Van on Fake A trigger", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_van_clear", Stance = EngagementStance.AGGRESSIVE_POKE, IsNoiseGroup = false, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite B", RoleAction = "Carry C4 safely into B Apartments and plant B", StagingSpotId = "tr_staging_b_apartments_house", ExecuteSpotId = "tr_exec_b_site_plant", Stance = EngagementStance.PASSIVE_HOLD, IsNoiseGroup = false, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite B", RoleAction = "Support B entry and lock Market Window", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.AGGRESSIVE_POKE, IsNoiseGroup = false, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "AWPer", TargetArea = "Bombsite A", RoleAction = "FAKE A: Throw smoke/flashes at A Ramp to force CT rotation", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_b_site_plant", Stance = EngagementStance.JIGGLE_INFO, IsNoiseGroup = true, RequiredUtilities = new() { "smoke", "flashbang", "decoy" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite A", RoleAction = "FAKE A: Make noise in Palace then cut rotations", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_b_market_push", Stance = EngagementStance.JIGGLE_INFO, IsNoiseGroup = true, RequiredUtilities = new() { "flashbang", "molotov" } }
                }
            },

            // 7. TR_FAKE_B_EXEC_A (Fake em B sem C4; Execução Real em A com C4!)
            new TrTacticBlueprint
            {
                TacticId = "TR_FAKE_B_EXEC_A",
                TacticName = "Fake B & Execução Real Bomb A",
                TacticSummary = "2 jogadores sem C4 simulam rush no Tapete B; Carrier + 2 executam sincronizados no Bomb A.",
                Tempo = RoundTempo.POKE_AND_ROTATE,
                StagingDuration = 12.0f,
                TacticType = TrTacticType.SPLIT_FAKE,
                TargetSite = "A",
                FakeSite = "B",
                RealSite = "A",
                Orders = new List<TrBotBlueprintOrder>
                {
                    new() { RoleKey = "EntryFragger", TargetArea = "Bombsite A", RoleAction = "Wait for B fake noise then entry A Ramp to Triple", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_triple_clear", Stance = EngagementStance.AGGRESSIVE_POKE, IsNoiseGroup = false, RequiredUtilities = new() { "flashbang", "molotov" } },
                    new() { RoleKey = "Rotator", TargetArea = "Bombsite A", RoleAction = "Carry C4 at A Ramp and plant Default A", StagingSpotId = "tr_staging_a_ramp", ExecuteSpotId = "tr_exec_a_site_default", Stance = EngagementStance.PASSIVE_HOLD, IsNoiseGroup = false, RequiredUtilities = new() { "smoke" } },
                    new() { RoleKey = "Anchor_1", TargetArea = "Bombsite A", RoleAction = "Exit Palace clearing Stairs and Jungle", StagingSpotId = "tr_staging_palace_room", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.AGGRESSIVE_POKE, IsNoiseGroup = false, RequiredUtilities = new() { "smoke", "flashbang" } },
                    new() { RoleKey = "AWPer", TargetArea = "Bombsite B", RoleAction = "FAKE B: Throw utilities in B Kitchen to draw CTs", StagingSpotId = "tr_staging_b_apartments_kitchen", ExecuteSpotId = "tr_exec_a_stairs_clear", Stance = EngagementStance.JIGGLE_INFO, IsNoiseGroup = true, RequiredUtilities = new() { "smoke", "flashbang", "decoy" } },
                    new() { RoleKey = "Anchor_2", TargetArea = "Bombsite B", RoleAction = "FAKE B: Pressure Underpass/B Short then lurk Mid", StagingSpotId = "tr_staging_underpass_top", ExecuteSpotId = "tr_exec_mid_connector_push", Stance = EngagementStance.JIGGLE_INFO, IsNoiseGroup = true, RequiredUtilities = new() { "flashbang", "hegrenade" } }
                }
            }
        };
    }
}
