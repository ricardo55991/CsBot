using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class TacticalCalloutSystem
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;

    // Rastreamento de Dano no Round: (attackerSlot, victimSlot) -> accumulatedDamage
    private readonly Dictionary<(int, int), int> _damageMatrix = new();
    private readonly Dictionary<int, string> _lastAttackerWeapon = new();
    private readonly Dictionary<int, string> _lastAttackerName = new();
    private readonly Dictionary<int, Vector> _lastAttackerPos = new();
    private readonly Dictionary<int, int> _lastAttackerHp = new();

    // Histórico de áudio e barulho recente por setor: sector -> timestamp
    private readonly Dictionary<string, float> _recentAudioBySector = new(StringComparer.OrdinalIgnoreCase);

    // Cooldowns anti-spam de callouts: key -> timestamp
    private readonly Dictionary<string, float> _calloutCooldowns = new(StringComparer.OrdinalIgnoreCase);

    // Rastreamento de atividades recentes para detecção de RUSH: sector -> lista de eventos recentes
    private readonly Dictionary<string, List<(float Time, int PlayerSlot, bool IsEnemy, bool IsGrenade)>> _recentSectorActivity = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _rushAlertedBombs = new(StringComparer.OrdinalIgnoreCase);

    private readonly Random _random = new();

    public TacticalCalloutSystem(BasePlugin plugin, MapProfileManager mapProfileManager, RoleManager roleManager)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
    }

    public void OnRoundStart()
    {
        _damageMatrix.Clear();
        _lastAttackerWeapon.Clear();
        _lastAttackerName.Clear();
        _lastAttackerPos.Clear();
        _lastAttackerHp.Clear();
        _recentAudioBySector.Clear();
        _calloutCooldowns.Clear();
        _recentSectorActivity.Clear();
        _rushAlertedBombs.Clear();
    }

    // ==============================================================================
    // 1. Rastreamento de Dano & Callout de Contato Visual e Recuo (Spot & Fallback)
    // ==============================================================================
    public void HandlePlayerHurt(EventPlayerHurt @event, TacticalPlan? currentPlan)
    {
        var victim = @event.Userid;
        var attacker = @event.Attacker;
        if (victim == null || !victim.IsValid) return;

        int dmg = @event.DmgHealth;
        int remainingHp = @event.Health;
        string weapon = @event.Weapon ?? "";

        // Se atacante é válido
        if (attacker != null && attacker.IsValid)
        {
            var key = (attacker.Slot, victim.Slot);
            _damageMatrix[key] = _damageMatrix.GetValueOrDefault(key, 0) + dmg;

            _lastAttackerWeapon[victim.Slot] = weapon;
            _lastAttackerName[victim.Slot] = attacker.PlayerName;
            _lastAttackerHp[victim.Slot] = attacker.PlayerPawn.Value?.Health ?? 100;

            if (attacker.PlayerPawn.Value?.AbsOrigin != null)
            {
                _lastAttackerPos[victim.Slot] = new Vector(
                    attacker.PlayerPawn.Value.AbsOrigin.X,
                    attacker.PlayerPawn.Value.AbsOrigin.Y,
                    attacker.PlayerPawn.Value.AbsOrigin.Z);
            }

            // Registra atividade sonora/tiro no setor do atacante
            if (attacker.PlayerPawn.Value?.AbsOrigin != null)
            {
                var attackerCp = _mapProfileManager.FindChokepointAt(
                    attacker.PlayerPawn.Value.AbsOrigin.X,
                    attacker.PlayerPawn.Value.AbsOrigin.Y,
                    attacker.PlayerPawn.Value.AbsOrigin.Z);
                if (attackerCp != null)
                {
                    RecordAudioActivity(attackerCp.Name, attacker.Slot, isEnemy: true, isGrenade: false);
                }
            }
        }

        // Se a vítima é um bot aliado vivo
        if (victim.IsBot && victim.PawnIsAlive)
        {
            CheckSpotAndFallbackCallout(victim, attacker, remainingHp, weapon, currentPlan);
            CheckInstantRushDetection(victim);
        }
    }

    private void CheckSpotAndFallbackCallout(CCSPlayerController victim, CCSPlayerController? attacker, int remainingHp, string weapon, TacticalPlan? plan)
    {
        if (victim.PlayerPawn.Value?.AbsOrigin == null) return;

        float now = Server.CurrentTime;
        var victimPos = victim.PlayerPawn.Value.AbsOrigin;
        var cp = _mapProfileManager.FindChokepointAt(victimPos.X, victimPos.Y, victimPos.Z);
        string sectorName = cp?.Name ?? "o setor";

        string cooldownKey = $"spot_{victim.Slot}_{sectorName}";
        if (_calloutCooldowns.TryGetValue(cooldownKey, out float lastCall) && now - lastCall < 10.0f)
        {
            return;
        }

        // Determina inimigos visíveis ou próximos no setor
        var allPlayers = Utilities.GetPlayers();
        var enemiesInSector = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team != victim.Team)
            .Where(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                        (p.PlayerPawn.Value.AbsOrigin - victimPos).Length() <= 900.0f)
            .ToList();

        int enemyCount = Math.Max(1, enemiesInSector.Count);
        bool hasAwp = weapon.Contains("awp", StringComparison.OrdinalIgnoreCase) ||
                      enemiesInSector.Any(e => HasAwpEquipped(e));

        // Verifica se portador da C4 está no setor
        bool hasC4Spotted = enemiesInSector.Any(e => HasC4Equipped(e));

        _calloutCooldowns[cooldownKey] = now;

        if (hasC4Spotted)
        {
            PrintTeamCallout(victim, $"💣 C4 VISTA na {sectorName}! O cara da bomba tá aqui!", "needbackup");
        }
        else if (hasAwp)
        {
            PrintTeamCallout(victim, $"⚠️ Cuidado, AWP cravado no {sectorName}! Não abre seco!", "takingfire");
        }
        else if (remainingHp < 55)
        {
            PrintTeamCallout(victim, $"Vi {enemyCount} na {sectorName}! Tomei tiro ({remainingHp} HP) e recuei pro Bomb!", "fallback");
        }
        else
        {
            PrintTeamCallout(victim, $"Contato na {sectorName}! Vi {enemyCount}, dei uns tiros e tô segurando o recuo!", "takingfire");
        }
    }

    // ==============================================================================
    // 2. Detecção Instantânea de Rush (Rush Alert)
    // ==============================================================================
    public void CheckInstantRushDetection(CCSPlayerController bot)
    {
        if (!bot.IsValid || !bot.PawnIsAlive || bot.PlayerPawn.Value?.AbsOrigin == null) return;

        var botPos = bot.PlayerPawn.Value.AbsOrigin;
        var cp = _mapProfileManager.FindChokepointAt(botPos.X, botPos.Y, botPos.Z);
        string sectorName = cp?.Name ?? "";
        string bombId = cp?.AssociatedBomb ?? (sectorName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A");

        if (_rushAlertedBombs.Contains(bombId)) return;

        float now = Server.CurrentTime;
        var allPlayers = Utilities.GetPlayers();

        // Conta inimigos vivos correndo ou muito próximos do mesmo chokepoint (raio <= 700u)
        var nearbyEnemies = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team != bot.Team)
            .Where(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                        (p.PlayerPawn.Value.AbsOrigin - botPos).Length() <= 750.0f)
            .ToList();

        // Checa histórico de passos / tiros nos últimos 3.5s no setor
        int recentEnemyEvents = 0;
        if (_recentSectorActivity.TryGetValue(sectorName, out var activities))
        {
            recentEnemyEvents = activities.Count(a => now - a.Time <= 3.5f && a.IsEnemy);
        }

        if (nearbyEnemies.Count >= 3 || (nearbyEnemies.Count >= 2 && recentEnemyEvents >= 3))
        {
            _rushAlertedBombs.Add(bombId);

            string targetSpot = !string.IsNullOrEmpty(sectorName) ? sectorName : $"Bomb {bombId}";
            PrintTeamCallout(bot, $"🚨 RUSH {bombId}!! Pelo menos 3 ou 4 rasgando o {targetSpot}, gira rápido!!", "needbackup");
        }
    }

    // ==============================================================================
    // 3. Callout Pós-Morte com Relatório de Dano (Death & Damage Callout)
    // ==============================================================================
    public void HandlePlayerDeath(EventPlayerDeath @event, TacticalPlan? currentPlan)
    {
        var victim = @event.Userid;
        var killer = @event.Attacker;
        if (victim == null || !victim.IsValid || !victim.IsBot) return;

        var victimTeam = victim.Team;
        string victimName = victim.PlayerName;
        int victimSlot = victim.Slot;

        // Posição de onde a vítima morreu
        Vector? deathPos = null;
        if (victim.PlayerPawn.Value?.AbsOrigin != null)
        {
            deathPos = new Vector(victim.PlayerPawn.Value.AbsOrigin.X, victim.PlayerPawn.Value.AbsOrigin.Y, victim.PlayerPawn.Value.AbsOrigin.Z);
        }

        // Delay humano natural de 1.0s para a call pós-morte
        _plugin.AddTimer(1.0f, () =>
        {
            string sector = "o setor";
            if (deathPos != null)
            {
                var cp = _mapProfileManager.FindChokepointAt(deathPos.X, deathPos.Y, deathPos.Z);
                sector = cp?.Name ?? "o bomb";
            }

            int killerSlot = killer?.Slot ?? -1;
            string killerName = killer?.PlayerName ?? "Inimigo";
            string weapon = @event.Weapon ?? "";

            // Verifica dano causado pela vítima no round
            int dmgDealtToKiller = killerSlot >= 0 ? _damageMatrix.GetValueOrDefault((victimSlot, killerSlot), 0) : 0;
            int killerHp = killer?.PlayerPawn.Value?.Health ?? 100;

            // Verifica se deixou alguém miado no round
            int maxDmg = 0;
            int miadoSlot = -1;
            foreach (var kvp in _damageMatrix)
            {
                if (kvp.Key.Item1 == victimSlot && kvp.Value > maxDmg)
                {
                    maxDmg = kvp.Value;
                    miadoSlot = kvp.Key.Item2;
                }
            }

            // Conta quantos inimigos estavam por perto na morte
            int enemiesNearby = 1;
            if (deathPos != null)
            {
                var players = Utilities.GetPlayers();
                enemiesNearby = players.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team != victimTeam &&
                                                   p.PlayerPawn.Value?.AbsOrigin != null &&
                                                   (p.PlayerPawn.Value.AbsOrigin - deathPos).Length() <= 800.0f);
                enemiesNearby = Math.Max(1, enemiesNearby);
            }

            // Monta callout pós-morte
            string calloutMsg;
            if (enemiesNearby >= 3)
            {
                string bombName = sector.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                calloutMsg = $"RUSH {bombName} confirmado! Passaram {enemiesNearby} pelo {sector}!";
            }
            else if (dmgDealtToKiller >= 45 || maxDmg >= 45)
            {
                int highDmg = Math.Max(dmgDealtToKiller, maxDmg);
                calloutMsg = $"Morri {sector}! Tem {enemiesNearby} lá, deixei um MUITO MIADO (-{highDmg} HP)!";
            }
            else if (weapon.Contains("awp", StringComparison.OrdinalIgnoreCase))
            {
                calloutMsg = $"Morri {sector}! AWP cravado lá ({killerHp} HP).";
            }
            else
            {
                calloutMsg = $"Morri {sector}! {killerName} tá lá ({killerHp} HP).";
            }

            PrintDeadTeamChat(victimTeam, victimName, calloutMsg);
        });
    }

    // ==============================================================================
    // 4. Callout de Som / Passos Próximos (Audio Cue Callout)
    // ==============================================================================
    public void HandleFootstep(EventPlayerFootstep @event)
    {
        var walker = @event.Userid;
        if (walker == null || !walker.IsValid || !walker.PawnIsAlive) return;

        var walkerPawn = walker.PlayerPawn.Value;
        if (walkerPawn == null || walkerPawn.AbsOrigin == null) return;

        var walkerPos = walkerPawn.AbsOrigin;
        var cp = _mapProfileManager.FindChokepointAt(walkerPos.X, walkerPos.Y, walkerPos.Z);
        string sectorName = cp?.Name ?? "";

        if (string.IsNullOrEmpty(sectorName)) return;

        // Registra som para a roleta contextual de smokes
        RecordAudioActivity(sectorName, walker.Slot, isEnemy: true, isGrenade: false);

        float now = Server.CurrentTime;
        string cooldownKey = $"audio_{sectorName}";
        if (_calloutCooldowns.TryGetValue(cooldownKey, out float lastAudioCall) && now - lastAudioCall < 15.0f)
        {
            return;
        }

        // Procura um bot aliado próximo (<= 750 unidades) que possa escutar
        var allPlayers = Utilities.GetPlayers();
        var listenerBot = allPlayers
            .Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive && p.Team != walker.Team)
            .Where(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                        (p.PlayerPawn.Value.AbsOrigin - walkerPos).Length() <= 750.0f)
            .FirstOrDefault();

        if (listenerBot != null)
        {
            _calloutCooldowns[cooldownKey] = now;
            PrintTeamCallout(listenerBot, $"👂 Ouvi passos perto de {sectorName}.", "holdpos");
        }
    }

    public void RecordAudioActivity(string sector, int playerSlot, bool isEnemy, bool isGrenade)
    {
        if (string.IsNullOrEmpty(sector)) return;

        float now = Server.CurrentTime;
        _recentAudioBySector[sector] = now;

        if (!_recentSectorActivity.ContainsKey(sector))
        {
            _recentSectorActivity[sector] = new List<(float, int, bool, bool)>();
        }

        var list = _recentSectorActivity[sector];
        list.Add((now, playerSlot, isEnemy, isGrenade));

        // Limpa eventos com mais de 10s
        list.RemoveAll(a => now - a.Time > 10.0f);
    }

    public bool HasRecentAudioNear(string sector, float maxSecondsAgo = 5.0f)
    {
        if (string.IsNullOrEmpty(sector)) return false;

        float now = Server.CurrentTime;
        if (_recentAudioBySector.TryGetValue(sector, out float time))
        {
            if (now - time <= maxSecondsAgo) return true;
        }

        // Procura setores com nomes semelhantes (ex: Jungle e Conector / Meio)
        foreach (var kvp in _recentAudioBySector)
        {
            if (now - kvp.Value <= maxSecondsAgo)
            {
                if (AreSectorsAdjacent(sector, kvp.Key))
                {
                    return true;
                }
            }
        }

        return false;
    }

    public string GetMostRecentActiveSector(float maxSecondsAgo = 5.0f)
    {
        float now = Server.CurrentTime;
        string bestSector = string.Empty;
        float bestTime = 0.0f;

        foreach (var kvp in _recentAudioBySector)
        {
            if (now - kvp.Value <= maxSecondsAgo && kvp.Value > bestTime)
            {
                bestTime = kvp.Value;
                bestSector = kvp.Key;
            }
        }

        return bestSector;
    }

    public static bool AreSectorsAdjacent(string sectorA, string sectorB)
    {
        if (string.Equals(sectorA, sectorB, StringComparison.OrdinalIgnoreCase)) return true;

        // Relações de adjacência comuns (Mirage, Dust2, Inferno)
        string a = sectorA.ToLowerInvariant();
        string b = sectorB.ToLowerInvariant();

        if ((a.Contains("jungle") || a.Contains("ligacao") || a.Contains("conector")) &&
            (b.Contains("meio") || b.Contains("janela") || b.Contains("conector") || b.Contains("jungle")))
        {
            return true;
        }

        if ((a.Contains("tapete") || a.Contains("van") || a.Contains("mercado")) &&
            (b.Contains("bomb b") || b.Contains("mercado") || b.Contains("l") || b.Contains("short")))
        {
            return true;
        }

        if ((a.Contains("palacio") || a.Contains("caverna") || a.Contains("rampa")) &&
            (b.Contains("bomb a") || b.Contains("tetris") || b.Contains("sanduiche")))
        {
            return true;
        }

        return false;
    }

    private static bool HasAwpEquipped(CCSPlayerController player)
    {
        var weaponServices = player.PlayerPawn.Value?.WeaponServices;
        var activeWeapon = weaponServices?.ActiveWeapon.Value;
        string wname = activeWeapon?.DesignerName ?? "";
        return wname.Contains("awp", StringComparison.OrdinalIgnoreCase);
    }

    private static bool HasC4Equipped(CCSPlayerController player)
    {
        var weaponServices = player.PlayerPawn.Value?.WeaponServices;
        if (weaponServices?.MyWeapons == null) return false;

        foreach (var handle in weaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.DesignerName != null && w.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }
        return false;
    }

    private static void PrintTeamCallout(CCSPlayerController bot, string message, string? radioCommand = null)
    {
        UtilityAndClockCoordinator.PrintTeamChatAndRadio(bot, bot.Team, bot.PlayerName, message, radioCommand);
    }

    public static void PrintDeadTeamChat(CsTeam team, string speakerName, string message)
    {
        string prefix = $" {ChatColors.Red}(Morto) {ChatColors.Green}{speakerName}{ChatColors.Default}: ";

        var players = Utilities.GetPlayers();
        foreach (var p in players)
        {
            if (p != null && p.IsValid && !p.IsHLTV && p.Team == team)
            {
                p.PrintToChat(prefix + message);
            }
        }
    }
}
