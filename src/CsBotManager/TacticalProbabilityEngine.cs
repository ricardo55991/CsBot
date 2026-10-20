using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class TacticalProbabilityEngine
{
    private readonly Random _random = new();
    private readonly Dictionary<string, int> _lastPlayedRoundTier2 = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _usedCheesePlays = new(StringComparer.OrdinalIgnoreCase);

    private const int Tier2CooldownRounds = 5;

    public void ResetMatch()
    {
        _lastPlayedRoundTier2.Clear();
        _usedCheesePlays.Clear();
    }

    public TacticalPlayDecision DecidePlayForRound(int currentRound, CsTeam team, BuyState buyState)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        int roll = _random.Next(100); // 0 a 99

        // Tier 3: Cheese / Jogadas Raras (5% -> roll 0 a 4)
        if (roll < 5 && buyState == BuyState.FULL_BUY)
        {
            var cheesePlay = TryPickTier3Play(currentRound, isCt);
            if (cheesePlay != null)
            {
                _usedCheesePlays.Add(cheesePlay.PlayId);
                Server.PrintToConsole($"[ProbabilityEngine] R{currentRound}: Sorteado TIER 3 CHEESE '{cheesePlay.PlayName}' (1x por partida).");
                return cheesePlay;
            }
        }

        // Tier 2: Variações Moderadas (23% -> roll 5 a 27)
        if (roll >= 5 && roll < 28 && buyState != BuyState.FULL_ECO)
        {
            var tier2Play = TryPickTier2Play(currentRound, isCt);
            if (tier2Play != null)
            {
                _lastPlayedRoundTier2[tier2Play.PlayId] = currentRound;
                Server.PrintToConsole($"[ProbabilityEngine] R{currentRound}: Sorteado TIER 2 '{tier2Play.PlayName}' (Cooldown de {Tier2CooldownRounds} rounds registrado).");
                return tier2Play;
            }
        }

        // Tier 1: Jogo Padrão Posicional (72% -> roll 28 a 99 ou fallback de cooldown)
        return GetTier1StandardPlay(isCt, buyState);
    }

    private TacticalPlayDecision GetTier1StandardPlay(bool isCt, BuyState buyState)
    {
        if (isCt)
        {
            return new TacticalPlayDecision
            {
                Tier = PlayTier.Tier1_Standard,
                PlayId = "CT_STANDARD_212",
                PlayName = "Defesa Padrão Posicional (2-1-2)",
                Description = "Controle posicional estrito com 2 defensores em cada bomb e 1 no meio.",
                Tempo = RoundTempo.SLOW_DEFAULT,
                CtDuo = CtDuoPlayType.None,
                TrTactic = TrTacticType.Default
            };
        }
        else
        {
            RoundTempo tempo = buyState == BuyState.FORCE_BUY ? RoundTempo.FAST_CONTACT : RoundTempo.SLOW_DEFAULT;
            return new TacticalPlayDecision
            {
                Tier = PlayTier.Tier1_Standard,
                PlayId = "TR_STANDARD_DEFAULT",
                PlayName = "Controle Padrão de Mapa (1-1-3)",
                Description = "Staging disciplinado com colheita de informação e preparação de utilitárias.",
                Tempo = tempo,
                CtDuo = CtDuoPlayType.None,
                TrTactic = TrTacticType.Default
            };
        }
    }

    private TacticalPlayDecision? TryPickTier2Play(int currentRound, bool isCt)
    {
        var candidates = isCt ? GetCtTier2CandidatePool() : GetTrTier2CandidatePool();

        // Filtra por cooldown: não pode ter sido jogado nos últimos 5 rounds
        var available = candidates
            .Where(c => !_lastPlayedRoundTier2.TryGetValue(c.PlayId, out int lastR) || (currentRound - lastR >= Tier2CooldownRounds))
            .ToList();

        if (available.Count == 0) return null;
        return available[_random.Next(available.Count)];
    }

    private TacticalPlayDecision? TryPickTier3Play(int currentRound, bool isCt)
    {
        var candidates = isCt ? GetCtTier3CandidatePool() : GetTrTier3CandidatePool();

        // Filtra por jogada única: não pode ter sido usada em nenhum round desta partida
        var available = candidates
            .Where(c => !_usedCheesePlays.Contains(c.PlayId))
            .ToList();

        if (available.Count == 0) return null;
        return available[_random.Next(available.Count)];
    }

    private List<TacticalPlayDecision> GetCtTier2CandidatePool() => new()
    {
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_DUO_DOMINIO_CAVERNA",
            PlayName = "Domínio Caverna em Dupla",
            Description = "Avanço coordenado com pop-flash de suporte na rampa A.",
            Tempo = RoundTempo.SLOW_DEFAULT,
            CtDuo = CtDuoPlayType.DominioCavernaRamp
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_DUO_DOMINIO_MEIO",
            PlayName = "Domínio Meio / Janela em Dupla",
            Description = "Pop-flash na janela e avanço agressivo para a catwalk.",
            Tempo = RoundTempo.SLOW_DEFAULT,
            CtDuo = CtDuoPlayType.DominioMeio
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_AGRESSIVO_TAPETE_B",
            PlayName = "Pressão de Saída Tapete B",
            Description = "Âncora e Rotator avançam no tapete para surpreender o lurker.",
            Tempo = RoundTempo.POKE_AND_ROTATE
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_CROSSFIRE_TRIPLA_NINJA",
            PlayName = "Crossfire Fechado Tripla & Ninja",
            Description = "Defesa passiva oculta esperando o avanço inimigo entrar na mira cruzada.",
            Tempo = RoundTempo.SLOW_DEFAULT
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_OVERWATCH_SHORT_L",
            PlayName = "Overwatch Meio / Catwalk",
            Description = "Reforço da meia-distância com suporte rápido para B e A.",
            Tempo = RoundTempo.SLOW_DEFAULT
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "CT_DEEP_CONECTOR_SETUP",
            PlayName = "Trava Avançada Conector / Rato",
            Description = "Pixel cruzado entre Jungle e Conector com mira no Underpass.",
            Tempo = RoundTempo.SLOW_DEFAULT
        }
    };

    private List<TacticalPlayDecision> GetTrTier2CandidatePool() => new()
    {
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_SPLIT_MEIO_B",
            PlayName = "Split Meio & Tapete para Bomb B",
            Description = "2 jogadores avançam pelo L / Catwalk enquanto 3 invadem pelo Tapete.",
            Tempo = RoundTempo.TIMED_EXECUTE
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_SPLIT_CONECTOR_A",
            PlayName = "Split Conector & Caverna para Bomb A",
            Description = "Invasão simultânea da Rampa A e do Conector para isolar os defensores.",
            Tempo = RoundTempo.TIMED_EXECUTE
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_POKE_FAKE_A_EXEC_B",
            PlayName = "Fake A com Execução B (Split Fake)",
            Description = "Grupo Barulho simula entrada em A enquanto a C4 caminha no shift para B.",
            Tempo = RoundTempo.POKE_AND_ROTATE,
            TrTactic = TrTacticType.SPLIT_FAKE
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_POKE_FAKE_B_EXEC_A",
            PlayName = "Fake B com Execução A (Split Fake)",
            Description = "Granadas e tiros no Tapete B para puxar rotação e entrada limpa no A.",
            Tempo = RoundTempo.POKE_AND_ROTATE,
            TrTactic = TrTacticType.SPLIT_FAKE
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_FAST_CONTACT_APARTS",
            PlayName = "Contato Rápido Silencioso Tapete B",
            Description = "Avanço rápido sem granadas para surpreender o âncora do B.",
            Tempo = RoundTempo.FAST_CONTACT
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier2_Moderate,
            PlayId = "TR_SLOW_DEFAULT_PICK",
            PlayName = "Padrão Lento Caça-Pique",
            Description = "Controle das três pontas aguardando CT cometer erro de avanço.",
            Tempo = RoundTempo.SLOW_DEFAULT
        }
    };

    private List<TacticalPlayDecision> GetCtTier3CandidatePool() => new()
    {
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier3_Cheese,
            PlayId = "CHEESE_4_STACK_B",
            PlayName = "Stack Tático 4 no Bomb B",
            Description = "Leitura arriscada de aposta com 4 defensores protegendo o Bomb B.",
            Tempo = RoundTempo.SLOW_DEFAULT
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier3_Cheese,
            PlayId = "CHEESE_SMOKE_PUSH_SURPRISE",
            PlayName = "Avanço Relâmpago através da Smoke",
            Description = "Avanço surpresa atravessando a própria fumaça de contenção no Meio.",
            Tempo = RoundTempo.FAST_CONTACT
        }
    };

    private List<TacticalPlayDecision> GetTrTier3CandidatePool() => new()
    {
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier3_Cheese,
            PlayId = "CHEESE_5_MAN_PALACE",
            PlayName = "Stack Surpresa 5 no Palácio",
            Description = "Toda a equipe silenciosa dentro do Palácio esperando o timing de explosão.",
            Tempo = RoundTempo.SLOW_DEFAULT
        },
        new TacticalPlayDecision
        {
            Tier = PlayTier.Tier3_Cheese,
            PlayId = "CHEESE_HERO_FAST_FLANK",
            PlayName = "Flanco Solitário Agressivo",
            Description = "Um bot corre imediatamente pelas costas para quebrar as rotações CT.",
            Tempo = RoundTempo.FAST_CONTACT
        }
    };
}
