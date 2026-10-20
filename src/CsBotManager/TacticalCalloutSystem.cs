using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class TacticalCalloutSystem
{
    private readonly CsBotManagerPlugin _plugin;
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

    public TacticalCalloutSystem(CsBotManagerPlugin plugin, MapProfileManager mapProfileManager, RoleManager roleManager)
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
    // HELPER CENTRAL DE PERCEPÇÃO LEGÍTIMA SEM WALLHACK POR RAIO (F-009 / BLOCO 1)
    // ==============================================================================
    public static bool CanBotPerceiveEnemy(
        CCSPlayerController bot,
        CCSPlayerController enemy,
        TacticalCalloutSystem? calloutSystem = null,
        MapProfileManager? mapProfile = null)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return false;
        if (enemy == null || !enemy.IsValid || !enemy.PawnIsAlive || enemy.Team == bot.Team) return false;

        var botPawn = bot.PlayerPawn.Value;
        var enemyPawn = enemy.PlayerPawn.Value;
        if (botPawn?.AbsOrigin == null || enemyPawn?.AbsOrigin == null) return false;

        var botPos = botPawn.AbsOrigin;
        var enemyPos = enemyPawn.AbsOrigin;

        float dist = (enemyPos - botPos).Length();
        if (dist > 2500.0f) return false;

        var botCp = mapProfile?.FindChokepointAt(botPos.X, botPos.Y, botPos.Z);
        var enemyCp = mapProfile?.FindChokepointAt(enemyPos.X, enemyPos.Y, enemyPos.Z);

        // 1. Linha de Visão / Spotted direto do engine
        bool isSpottedByMask = false;
        try
        {
            var mask = enemyPawn.EntitySpottedState.SpottedByMask;
            int idx = bot.Slot / 32;
            int bit = bot.Slot % 32;
            if (idx >= 0 && idx < mask.Length)
            {
                isSpottedByMask = (mask[idx] & (1u << bit)) != 0;
            }
        }
        catch { }

        // 2. Cone de Visão (FOV ~95°, +/- 47.5 graus do EyeAngles do bot)
        bool isInFov = false;
        if (botPawn.EyeAngles != null)
        {
            float botYaw = botPawn.EyeAngles.Y;
            float dx = enemyPos.X - botPos.X;
            float dy = enemyPos.Y - botPos.Y;
            float angleToEnemy = (float)(Math.Atan2(dy, dx) * 180.0 / Math.PI);
            float diff = angleToEnemy - botYaw;
            while (diff < -180.0f) diff += 360.0f;
            while (diff > 180.0f) diff -= 360.0f;

            if (Math.Abs(diff) <= 47.5f)
            {
                isInFov = true;
            }
        }

        bool smokeBlocking = calloutSystem != null && botCp != null && enemyCp != null &&
                             calloutSystem.HasRecentSmokeLikelyBetween(botCp.Name, enemyCp.Name, 18.0f);

        bool hasGeometricValidity = botCp != null && enemyCp != null &&
                                    (string.Equals(botCp.Name, enemyCp.Name, StringComparison.OrdinalIgnoreCase) ||
                                     AreSectorsAdjacent(botCp.Name, enemyCp.Name));

        // Visual legítimo: FOV + (spotted OU geometria plausível) + sem bloqueio recente de smoke
        if (isInFov && (isSpottedByMask || hasGeometricValidity) && !smokeBlocking)
        {
            return true;
        }

        // 3. Percepção Sonora: Inimigo emitiu som audível (Footstep, WeaponFire, Dano) naquele setor nos últimos 4.0s
        if (calloutSystem != null && enemyCp != null)
        {
            if (calloutSystem.HasRecentEnemyAudioInSector(enemyCp.Name, 4.0f))
            {
                return true;
            }
        }

        return false;
    }

    public bool HasRecentEnemyAudioInSector(string sector, float maxSecondsAgo = 4.0f)
    {
        if (string.IsNullOrEmpty(sector)) return false;
        float now = Server.CurrentTime;

        if (_recentSectorActivity.TryGetValue(sector, out var activities))
        {
            lock (activities)
            {
                return activities.Any(a => now - a.Time <= maxSecondsAgo && a.IsEnemy && !a.IsGrenade);
            }
        }
        return false;
    }

    public bool HasRecentSmokeLikelyBetween(string sectorA, string sectorB, float maxSecondsAgo = 18.0f)
    {
        if (string.IsNullOrEmpty(sectorA) || string.IsNullOrEmpty(sectorB)) return false;
        float now = Server.CurrentTime;

        foreach (var kvp in _recentSectorActivity)
        {
            string sector = kvp.Key;
            if (!string.Equals(sector, sectorA, StringComparison.OrdinalIgnoreCase) &&
                !string.Equals(sector, sectorB, StringComparison.OrdinalIgnoreCase) &&
                !AreSectorsAdjacent(sector, sectorA) &&
                !AreSectorsAdjacent(sector, sectorB))
            {
                continue;
            }

            var events = kvp.Value;
            lock (events)
            {
                bool hasRecentSmoke = events.Any(e => e.IsGrenade && now - e.Time <= maxSecondsAgo);
                if (hasRecentSmoke)
                {
                    return true;
                }
            }
        }

        return false;
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

            // Registra atividade sonora/tiro no setor do atacante (isEnemy true apenas se time for oposto)
            if (attacker.PlayerPawn.Value?.AbsOrigin != null)
            {
                var attackerCp = _mapProfileManager.FindChokepointAt(
                    attacker.PlayerPawn.Value.AbsOrigin.X,
                    attacker.PlayerPawn.Value.AbsOrigin.Y,
                    attacker.PlayerPawn.Value.AbsOrigin.Z);
                if (attackerCp != null)
                {
                    bool isAttackerEnemy = attacker.Team != victim.Team;
                    RecordAudioActivity(attackerCp.Name, attacker.Slot, isEnemy: isAttackerEnemy, isGrenade: false);
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

        // Determina inimigos perceptíveis no setor de forma legítima (sem raio cego)
        var allPlayers = Utilities.GetPlayers();
        var enemiesInSector = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team != victim.Team)
            .Where(p => CanBotPerceiveEnemy(victim, p, this, _mapProfileManager))
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

        // Conta inimigos vivos perceptíveis no chokepoint
        var nearbyEnemies = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team != bot.Team)
            .Where(p => CanBotPerceiveEnemy(bot, p, this, _mapProfileManager))
            .ToList();

        // Checa histórico de passos / tiros nos últimos 3.5s no setor
        int recentEnemyEvents = 0;
        if (_recentSectorActivity.TryGetValue(sectorName, out var activities))
        {
            lock (activities)
            {
                recentEnemyEvents = activities.Count(a => now - a.Time <= 3.5f && a.IsEnemy);
            }
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

        // Delay humano natural de 1.0s para a call pós-morte rastreado pelo timer central do round (F-006 / F-012)
        _plugin.AddRoundTimer(1.0f, () =>
        {
            if (victim == null || !victim.IsValid) return;

            string sector = "o setor";
            if (deathPos != null)
            {
                var cp = _mapProfileManager.FindChokepointAt(deathPos.X, deathPos.Y, deathPos.Z);
                sector = cp?.Name ?? "o bomb";
            }

            int killerSlot = (killer != null && killer.IsValid) ? killer.Slot : -1;
            string killerName = (killer != null && killer.IsValid) ? killer.PlayerName : "Inimigo";
            string weapon = @event.Weapon ?? "";

            // Verifica dano causado pela vítima no round
            int dmgDealtToKiller = killerSlot >= 0 ? _damageMatrix.GetValueOrDefault((victimSlot, killerSlot), 0) : 0;
            int killerHp = (killer != null && killer.IsValid) ? killer.PlayerPawn.Value?.Health ?? 100 : 100;

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
    // 4. Callout de Som / Passos Próximos (Audio Cue Callout - Bloco 1 / F-009)
    // ==============================================================================
    public void HandleWeaponFire(EventWeaponFire @event)
    {
        var shooter = @event.Userid;
        if (shooter == null || !shooter.IsValid || !shooter.PawnIsAlive) return;

        var shooterPos = shooter.PlayerPawn.Value?.AbsOrigin;
        if (shooterPos == null) return;

        var cp = _mapProfileManager.FindChokepointAt(shooterPos.X, shooterPos.Y, shooterPos.Z);
        string sectorName = cp?.Name ?? string.Empty;
        if (string.IsNullOrEmpty(sectorName)) return;

        var allPlayers = Utilities.GetPlayers();
        bool anyEnemyListenerNearby = allPlayers.Any(p =>
            p != null && p.IsValid && p.IsBot && p.PawnIsAlive && p.Team != shooter.Team &&
            p.PlayerPawn.Value?.AbsOrigin != null &&
            (p.PlayerPawn.Value.AbsOrigin - shooterPos).Length() <= 1200.0f);

        RecordAudioActivity(sectorName, shooter.Slot, isEnemy: anyEnemyListenerNearby, isGrenade: false);
    }

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

        // Procura um bot adversário próximo (<= 750 unidades) que possa escutar
        var allPlayers = Utilities.GetPlayers();
        var listenerBot = allPlayers
            .Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive && p.Team != walker.Team)
            .Where(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                        (p.PlayerPawn.Value.AbsOrigin - walkerPos).Length() <= 750.0f)
            .FirstOrDefault();

        if (listenerBot != null)
        {
            // O passo veio de um ADVERSÁRIO em relação ao ouvinte: registra como inimigo
            RecordAudioActivity(sectorName, walker.Slot, isEnemy: true, isGrenade: false);

            float now = Server.CurrentTime;
            string cooldownKey = $"audio_{sectorName}";
            if (!_calloutCooldowns.TryGetValue(cooldownKey, out float lastAudioCall) || now - lastAudioCall >= 15.0f)
            {
                _calloutCooldowns[cooldownKey] = now;
                PrintTeamCallout(listenerBot, $"👂 Ouvi passos perto de {sectorName}.", "holdpos");
            }
        }
        else
        {
            // O passo veio de um ALIADO ou nenhum inimigo estava no alcance: NUNCA marcar como isEnemy: true
            RecordAudioActivity(sectorName, walker.Slot, isEnemy: false, isGrenade: false);
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
        lock (list)
        {
            list.Add((now, playerSlot, isEnemy, isGrenade));
            // Limpa eventos com mais de 10s
            list.RemoveAll(a => now - a.Time > 10.0f);
        }
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
        if (activeWeapon != null && activeWeapon.IsValid)
        {
            string wname = activeWeapon.DesignerName ?? "";
            return wname.Contains("awp", StringComparison.OrdinalIgnoreCase);
        }
        return false;
    }

    private static bool HasC4Equipped(CCSPlayerController player)
    {
        var weaponServices = player.PlayerPawn.Value?.WeaponServices;
        if (weaponServices?.MyWeapons == null) return false;

        foreach (var handle in weaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName) && w.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
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
