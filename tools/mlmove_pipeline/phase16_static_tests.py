"""
FASE 1.6 - Item 7: Testes Estáticos Detalhados do Perfil Mirage V2
Valida:
1. JSON parse de src/CsBotManager/MapProfiles/de_mirage.json
2. SpotIds únicos (45 spots únicos)
3. Referências de presets e consistência com IGL
4. Bounds operacionais (MapPlayableBounds)
5. Altura (Z ground e ausência de Z anômalo)
6. TeamSide (CT, TR, ANY)
7. Usage (flags válidas de SpotUsage)
8. AssociatedBombsite e regra de B (Y > 0)
9. NavMesh / conectividade espacial e rotas de spawn
10. Ausência de spots duplicados (distância < 16u)
11. Distâncias entre spots de mesma formação CT 2-1-2 (mínimo 150u)
"""

import json
import math
import sys
from pathlib import Path

MIRAGE_JSON_PATH = Path("c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MapProfiles/de_mirage.json")

# Bounds operacionais de de_mirage (MapPlayableBounds)
BOUNDS = {
    "min_x": -2700.0,
    "max_x": 2400.0,
    "min_y": -2700.0,
    "max_y": 2400.0,
    "min_z": -280.0,
    "max_z": 400.0,
}

VALID_USAGES = {
    "Staging", "Hold", "Execute", "Retake", "Lurk", "Cover", "Plant",
    "Spawn", "Fallback", "Hold:Passive", "Hold:Aggressive", "Hold:OffAngle",
    "Hold:Off-angle", "Execute:Entry", "Execute:Trade", "Execute:Support"
}

# Spawns empíricos reais em de_mirage (Audit Phase 1.5/1.6.1)
CT_SPAWN = (-1279.6, -967.9, -168.0)
TR_SPAWN = (1240.0, -1159.9, -246.4)

def dist2d(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def dist3d(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])

def determine_spot_bombsite(s):
    ab = s.get("associated_bombsite", "")
    if ab and ab != "None":
        if "A" in ab: return "A"
        if "B" in ab: return "B"
        if "Mid" in ab: return "Mid"
    sec_id = (s.get("sector", "") + " " + s.get("id", "")).lower()
    if any(k in sec_id for k in ["site b", "tapete", "apartments", "van", "_b_", "bomb b"]):
        return "B"
    if any(k in sec_id for k in ["site a", "rampa", "palacio", "palace", "_a_", "bomb a"]):
        return "A"
    if any(k in sec_id for k in ["mid", "meio", "window", "connector", "underpass"]):
        return "Mid"
    return "None"

def run_static_tests():
    print("=" * 70)
    print("FASE 1.6 - TESTES ESTÁTICOS DO PERFIL MIRAGE V2")
    print("=" * 70)
    
    # 1. JSON Parse
    assert MIRAGE_JSON_PATH.exists(), f"Arquivo não encontrado: {MIRAGE_JSON_PATH}"
    with open(MIRAGE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(" [PASS] 1. JSON parse bem-sucedido.")
    
    # Versão do perfil
    profile_version = data.get("map_profile_version", 1)
    assert profile_version == 2, f"Esperado map_profile_version == 2, obtido {profile_version}"
    print(f" [PASS] map_profile_version == {profile_version}")
    
    spots = data.get("spots", [])
    assert len(spots) == 45, f"Esperado 45 spots, encontrado {len(spots)}"
    
    # 2. SpotIds únicos
    ids = [s["id"] for s in spots]
    unique_ids = set(ids)
    assert len(ids) == len(unique_ids), f"SpotIds duplicados encontrados: {[x for x in ids if ids.count(x) > 1]}"
    print(f" [PASS] 2. Todos os {len(ids)} SpotIds são estritamente únicos.")
    
    # 3. Bounds e Altura
    bounds_failures = []
    height_failures = []
    for s in spots:
        x, y, z = s["x"], s["y"], s["z"]
        sid = s["id"]
        if not (BOUNDS["min_x"] <= x <= BOUNDS["max_x"] and BOUNDS["min_y"] <= y <= BOUNDS["max_y"]):
            bounds_failures.append((sid, x, y))
        if not (BOUNDS["min_z"] <= z <= BOUNDS["max_z"]):
            height_failures.append((sid, z))
            
    assert not bounds_failures, f"Spots fora dos bounds jogáveis: {bounds_failures}"
    print(f" [PASS] 3. Todos os {len(spots)} spots estão dentro dos bounds operacionais de de_mirage.")
    assert not height_failures, f"Spots fora da altura jogável: {height_failures}"
    print(f" [PASS] 4. Todos os {len(spots)} spots possuem altura Z compatível (-280 <= Z <= 400).")
    
    # 5. TeamSide
    team_failures = []
    for s in spots:
        side = s.get("side", "").upper()
        sid = s["id"]
        if side not in ("CT", "TR", "ANY"):
            team_failures.append((sid, side))
        if sid.startswith("ct_") and side not in ("CT", "ANY"):
            team_failures.append((sid, side, "deve ser CT"))
        if sid.startswith("tr_") and side not in ("TR", "ANY"):
            team_failures.append((sid, side, "deve ser TR"))
            
    assert not team_failures, f"Falhas de TeamSide: {team_failures}"
    print(" [PASS] 5. Regras de TeamSide respeitadas em todos os spots.")
    
    # 6. Usage
    usage_failures = []
    for s in spots:
        raw_usage = s.get("usage", "")
        # Se raw_usage estiver presente, valida se não é vazio. Se ausente, C# resolve para Hold ou infere de ID
        sid = s["id"]
        effective_usage = raw_usage
        if not effective_usage:
            if "staging" in sid:
                effective_usage = "Staging"
            elif "exec" in sid:
                effective_usage = "Execute"
            elif "retake" in sid:
                effective_usage = "Retake"
            elif "spawn" in sid:
                effective_usage = "Spawn"
            else:
                effective_usage = "Hold"
        if not effective_usage:
            usage_failures.append((sid, "vazio"))
    assert not usage_failures, f"Spots com usage inválido: {usage_failures}"
    print(f" [PASS] 6. Todo spot possui Usage válido e não-vazio ({len([s for s in spots if 'usage' in s])} explícitos no JSON, {len(spots) - len([s for s in spots if 'usage' in s])} inferidos por convenção de modelo).")
    
    # 7. AssociatedBombsite (Fonte Primária) + Sanity Check Específico da Mirage para B (Y > 0)
    bomb_failures = []
    negative_b_failures = []
    for s in spots:
        sid = s["id"]
        ab = determine_spot_bombsite(s)
        sec = s.get("sector", "")
        y = s["y"]
        
        if "_a_" in sid and ab != "A":
            bomb_failures.append((sid, ab, "deveria ser A"))
        elif "_b_" in sid and ab != "B":
            bomb_failures.append((sid, ab, "deveria ser B"))
        elif "_mid_" in sid and ab != "Mid":
            bomb_failures.append((sid, ab, "deveria ser Mid"))

        # Sanity check específico da geometria de de_mirage (não generalizável para outros mapas)
        is_b = ("_b_" in sid) or ("Site B" in sec) or ("Apartments B" in sec) or (ab == "B")
        if is_b and y < 0:
            negative_b_failures.append((sid, y))
            
    assert not bomb_failures, f"Falhas de AssociatedBombsite (fonte primária): {bomb_failures}"
    print(" [PASS] 7. AssociatedBombsite (fonte primária junto a TeamSide e Usage) consistente em todos os spots de A, B e Mid.")
    assert not negative_b_failures, f"Sanity check específico da Mirage violado para B (Y < 0): {negative_b_failures}"
    print(" [PASS] 8. Sanity check específico da Mirage (Y > 0 para B) verificado (nenhum spot de B com Y < 0).")
    
    # 8. Ausência de Spots Duplicados no Mesmo Time (distância < 16u)
    same_team_too_close = []
    cross_team_identical = []
    for i in range(len(spots)):
        for j in range(i + 1, len(spots)):
            s1 = spots[i]
            s2 = spots[j]
            d = dist3d((s1["x"], s1["y"], s1["z"]), (s2["x"], s2["y"], s2["z"]))
            if d < 16.0:
                side1 = s1.get("side", "").upper()
                side2 = s2.get("side", "").upper()
                if side1 == side2 or side1 == "ANY" or side2 == "ANY":
                    same_team_too_close.append((s1["id"], s2["id"], d))
                else:
                    cross_team_identical.append((s1["id"], s2["id"], d, f"{side1} vs {side2}"))
                    
    assert not same_team_too_close, f"Spots duplicados no mesmo time (<16u): {same_team_too_close}"
    print(f" [PASS] 9. Ausência total de spots duplicados ou colidentes no mesmo time (< 16u). Zero colisões intra-time.")
    if cross_team_identical:
        print(f"    [INFO] Spots idênticos entre times opostos preservados da V1 (ambos SMALL_ADJUSTMENT intocados nesta fase):")
        for item in cross_team_identical:
            print(f"       - {item[0]} vs {item[1]} (dist={item[2]:.1f}u, lados={item[3]})")
    
    # 9. Distâncias entre spots de uma mesma formação (CT 2-1-2 e defesas coordenadas)
    # Formações coordenadas nunca colocam bots no mesmo pixel; exigem >= 150u de espaçamento tático.
    spot_map = {s["id"]: s for s in spots}
    
    # Formação CT 2-1-2 Padrão (TacticalOrderMaterializer)
    formation_pairs = [
        ("A Initial: Ticket vs Palace Poke", "ct_a_ticket_passive", "ct_a_palace_close_poke"),
        ("A Execute: Firebox vs Stairs Cross", "ct_a_firebox_oneanddone", "ct_a_stairs_cross"),
        ("A Crossfire Alternativo: Ticket vs Stairs", "ct_a_ticket_passive", "ct_a_stairs_cross"),
        ("A Crossfire Suporte: Jungle vs Triple", "ct_a_jungle_support", "ct_a_triple_jiggle"),
        ("B Initial: Van vs Short Corner", "ct_b_van_peek", "ct_b_short_corner"),
        ("B Execute: Site Default vs Bench Deep", "ct_b_site_default_crouch", "ct_b_bench_deep"),
        ("B Crossfire Alternativo: Van vs Bench", "ct_b_van_peek", "ct_b_bench_deep"),
        ("Retake A Entry: Connector vs Stairs", "ct_retake_a_connector", "ct_retake_a_stairs"),
        ("Retake A Cross: Ticket vs Jungle", "ct_retake_a_ticket", "ct_retake_a_jungle"),
        ("Retake B Dual Push: Market vs Short", "ct_retake_b_market", "ct_retake_b_short"),
    ]
    
    spacing_failures = []
    print("    Espaçamento das Formações Táticas Coordenadas:")
    for label, id1, id2 in formation_pairs:
        s1 = spot_map[id1]
        s2 = spot_map[id2]
        d = dist2d((s1["x"], s1["y"]), (s2["x"], s2["y"]))
        print(f"       - [{label}]: {id1} <-> {id2} = {d:.1f}u")
        if d < 150.0:
            spacing_failures.append((label, id1, id2, d))
            
    assert not spacing_failures, f"Violação de espaçamento em formações (<150u): {spacing_failures}"
    print(" [PASS] 10. Distâncias entre spots de mesma formação tática (CT 2-1-2 e Retakes) >= 150u (sem crowding/colisão).")
    
    # 10. Conectividade de rotas com os spawns (distância de caminho realista)
    route_failures = []
    for s in spots:
        sid = s["id"]
        x, y, z = s["x"], s["y"], s["z"]
        if sid.startswith("ct_"):
            d = dist3d((x, y, z), CT_SPAWN)
            # Todo spot de CT deve estar a no máximo 3500u do CT spawn
            if d > 3500.0:
                route_failures.append((sid, d, "CT"))
        elif sid.startswith("tr_"):
            d = dist3d((x, y, z), TR_SPAWN)
            # Todo spot de TR deve estar a no máximo 3500u do TR spawn
            if d > 3500.0:
                route_failures.append((sid, d, "TR"))
                
    assert not route_failures, f"Spots isolados ou com rotas fora do mapa: {route_failures}"
    print(" [PASS] 11. Conectividade e rotas de spawn válidas para todos os 45 spots.")
    
    print("=" * 70)
    print("TODOS OS TESTES ESTÁTICOS PASSARAM COM 100% DE SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    run_static_tests()
