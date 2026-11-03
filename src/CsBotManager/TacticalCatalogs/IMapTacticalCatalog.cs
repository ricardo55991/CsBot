namespace CsBotManager;

/// <summary>
/// Contrato para catálogos de táticas macro específicas por mapa (ex.: de_mirage, de_dust2, de_inferno).
/// Permite adicionar novos mapas sem alterar o motor matemático TacticalUtilityIglEngine.
/// </summary>
public interface IMapTacticalCatalog
{
    string MapName { get; }
    IReadOnlyList<CtTacticBlueprint> CtTactics { get; }
    IReadOnlyList<TrTacticBlueprint> TrTactics { get; }

    /// <summary>
    /// Roteamento léxico específico do mapa (gírias/callouts locais como "tapete", "palácio", "caverna" na Mirage,
    /// ou "banana", "xuxa", "nip" na Inferno, ou "fundo", "varanda", "escuro" na Dust2).
    /// </summary>
    bool TryRouteMapSpecificLexicalCall(CounterStrikeSharp.API.Modules.Utils.CsTeam team, string normalizedText, out string matchedTacticId, out string matchedReason);
}
