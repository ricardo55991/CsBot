#!/usr/bin/env python3
"""
Crawler em Grafo (Efeito Bola de Neve) — Aquisição de demos Premier/MM de Mirage
em faixas de rating amador (8.000 – 18.500 CS Rating).

Fonte: API pública do Leetify (api-public.cs-prod.leetify.com).

Design:
- BFS sobre SteamIDs: cada partida indexada expõe os 10 participantes,
  que entram na fila de exploração.
- Filtro por mapa (de_mirage) e por faixa de rating do lobby.
- Captura do link oficial de replay da Valve (replay*.valve.net) quando presente.
- Rate limiting respeitoso + backoff exponencial em HTTP 429.
- Suporte a chave gratuita do Leetify via variável de ambiente LEETIFY_API_KEY
  (header `_leetify_key`), que eleva substancialmente o limite de requisições.

Modos:
  --discover   apenas mapeia partidas candidatas (JSON), não baixa nada
  --download   baixa e descompacta (.bz2 ou .gz) as demos aprovadas no manifesto

Governança:
- Não inventa dados: registra proveniência (REAL_DISCOVERED) e motivo de rejeição.
- Nunca sobrescreve demos existentes.
- Toda escrita é idempotente e registrada em log JSON.
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import json
import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

# ------------------------------------------------------------------------------
# Configuração
# ------------------------------------------------------------------------------

LEETIFY_BASE = "https://api-public.cs-prod.leetify.com"
STEAM_XML = "https://steamcommunity.com/id/{slug}/?xml=1"

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "datasets" / "amateur_mirage_acquisition"
RAW_DIR = OUT_DIR / "raw_demos"
STATE_DIR = OUT_DIR / "state"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Faixas alvo (CS Rating Premier) — conforme especificação do usuário
RATING_BANDS = [
    {"name": "F1_GOLD4_AK1", "min": 8000, "max": 11000},
    {"name": "F2_AKX_SHERIFF", "min": 12000, "max": 15500},
    {"name": "F3_EAGLE_LEM", "min": 16000, "max": 18500},
]

TARGET_MAP = "de_mirage"
TARGET_PREFIX = "de_mirage"

DEFAULT_SEEDS = [
    "76561199095726404",
    "76561198118241395",  # meriwether / leLeandro
    "76561198350768015",  # MiawTheKat
    "76561198351555042",  # japacobra
    "76561199252179372",  # donkcs2 / Demoman
    "76561199159934845",  # theIastofus / cool guy
]


# ------------------------------------------------------------------------------
# Cliente HTTP com backoff
# ------------------------------------------------------------------------------

class RateLimitedClient:
    def __init__(self, api_key: Optional[str] = None, min_interval: float = 6.0):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA, "Accept": "application/json"})
        if api_key:
            self.session.headers["_leetify_key"] = api_key
        self.api_key = api_key
        self.min_interval = min_interval
        self._last_call = 0.0
        self.stats = {"requests": 0, "ok": 0, "429": 0, "404": 0, "errors": 0}

    def _throttle(self):
        wait = self.min_interval - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    def get_json(self, url: str, max_retries: int = 5) -> Optional[Any]:
        backoff = 20.0
        for attempt in range(max_retries):
            self._throttle()
            self.stats["requests"] += 1
            try:
                r = self.session.get(url, timeout=25)
            except Exception:
                self.stats["errors"] += 1
                time.sleep(backoff)
                backoff *= 2
                continue

            if r.status_code == 200:
                self.stats["ok"] += 1
                try:
                    return r.json()
                except ValueError:
                    self.stats["errors"] += 1
                    return None
            if r.status_code == 429:
                self.stats["429"] += 1
                retry_after = r.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                print(f"    [429] rate limit — aguardando {delay:.0f}s (tentativa {attempt+1}/{max_retries})")
                time.sleep(delay)
                backoff *= 1.8
                continue
            if r.status_code == 404:
                self.stats["404"] += 1
                return None
            self.stats["errors"] += 1
            print(f"    [HTTP {r.status_code}] {url}")
            return None
        return None


# ------------------------------------------------------------------------------
# Resolução de SteamID
# ------------------------------------------------------------------------------

def resolve_steam_id(raw: str, client: RateLimitedClient) -> Optional[str]:
    raw = str(raw).strip().rstrip("/")
    if raw.isdigit() and len(raw) == 17:
        return raw
    m = re.search(r"steamcommunity\.com/(?:id|profiles)/([^/]+)", raw)
    slug = m.group(1) if m else raw
    if slug.isdigit() and len(slug) == 17:
        return slug
    try:
        r = client.session.get(STEAM_XML.format(slug=slug), timeout=20)
        if r.status_code == 200:
            found = re.search(r"<steamID64>(\d{17})</steamID64>", r.text)
            if found:
                return found.group(1)
    except Exception:
        pass
    return None


# ------------------------------------------------------------------------------
# Estruturas
# ------------------------------------------------------------------------------

@dataclass
class CandidateMatch:
    game_id: str
    map_name: str
    rating: Optional[int]
    band: Optional[str]
    replay_url: Optional[str]
    discovered_from: str
    data_source: List[str]
    players: List[str] = field(default_factory=list)
    played_at: Optional[str] = None
    provenance: str = "REAL_DISCOVERED"


def classify_band(rating: Optional[int]) -> Optional[str]:
    if rating is None:
        return None
    for b in RATING_BANDS:
        if b["min"] <= rating <= b["max"]:
            return b["name"]
    return None


def normalize_map(name: Optional[str]) -> str:
    return (name or "").replace("de_", "").lower()


# ------------------------------------------------------------------------------
# Extração de campos de payloads variáveis do Leetify
# ------------------------------------------------------------------------------

REPLAY_KEYS = ("replay_url", "replayUrl", "demo_url", "demoUrl", "valve_replay_url")
RATING_KEYS = ("skill_level", "rating", "rank", "avg_rank", "cs_rating", "premier_rating")


def deep_find(obj: Any, keys: Iterable[str], max_depth: int = 5) -> Optional[Any]:
    """Busca heurística por primeira chave encontrada em payload aninhado."""
    keys = set(keys)
    stack = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > max_depth:
            continue
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k in keys and isinstance(v, (str, int, float)) and v not in ("", None):
                    return v
                if isinstance(v, (dict, list)):
                    stack.append((v, depth + 1))
        elif isinstance(cur, list):
            for v in cur[:50]:
                if isinstance(v, (dict, list)):
                    stack.append((v, depth + 1))
    return None


def extract_players(details: Any) -> List[str]:
    """Coleta SteamIDs dos participantes de qualquer estrutura de partida."""
    out: List[str] = []
    seen = set()

    def walk(node, depth=0):
        if depth > 6:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("steam64_id", "steam_id", "steamId", "steamid64", "steam64") and isinstance(v, str):
                    if v.isdigit() and len(v) == 17 and v not in seen:
                        seen.add(v)
                        out.append(v)
                elif isinstance(v, (dict, list)):
                    walk(v, depth + 1)
        elif isinstance(node, list):
            for v in node[:60]:
                walk(v, depth + 1)

    walk(details)
    return out


# ------------------------------------------------------------------------------
# Crawler
# ------------------------------------------------------------------------------

def load_state() -> Dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / "crawler_state.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"visited_players": [], "visited_matches": [], "candidates": []}


def save_state(state: Dict[str, Any]):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_DIR / "crawler_state.json.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_DIR / "crawler_state.json")


def crawl(
    seeds: List[str],
    client: RateLimitedClient,
    max_players: int,
    max_matches_inspected: int,
    per_player_limit: int = 20,
) -> Dict[str, Any]:
    state = load_state()
    visited_players = set(state.get("visited_players", []))
    visited_matches = set(state.get("visited_matches", []))
    candidates: List[Dict[str, Any]] = state.get("candidates", [])

    queue: deque = deque()
    for s in seeds:
        sid = resolve_steam_id(s, client)
        if sid:
            print(f"[seed] {s} -> {sid}")
            queue.append((sid, "seed"))
        else:
            print(f"[seed] {s} -> NAO_RESOLVIDO")

    inspected = 0
    players_done = 0

    while queue and players_done < max_players and inspected < max_matches_inspected:
        steam_id, origin = queue.popleft()
        if steam_id in visited_players:
            continue
        visited_players.add(steam_id)
        players_done += 1

        # CONFIRMADO em 2026-11-09: o identificador exigido e' `steam64_id`
        # (query string). `steamId`, `steamId64`, `steamid64` etc. retornam
        # 200 {"error":"At least one identifier must be provided"} e
        # `/v3/players/{id}` nao existe (404). Perfil inexistente -> 404.
        payload = client.get_json(f"{LEETIFY_BASE}/v3/profile/matches?steam64_id={steam_id}")
        if payload is None:
            if client.stats["429"] > 0 and client.stats["ok"] == 0:
                print("[abort] rate limit persistente sem nenhuma chamada bem-sucedida.")
                break
            continue

        # Extrair lista de partidas de qualquer estrutura
        games = None
        if isinstance(payload, dict):
            for key in ("games", "recent_matches", "matches", "recentGames"):
                if isinstance(payload.get(key), list):
                    games = payload[key]
                    break
        if games is None and isinstance(payload, list):
            games = payload
        if not games:
            continue

        for g in games[:per_player_limit]:
            if inspected >= max_matches_inspected:
                break
            if not isinstance(g, dict):
                continue
            game_id = str(g.get("id") or g.get("game_id") or g.get("match_id") or "")
            if not game_id or game_id in visited_matches:
                continue
            visited_matches.add(game_id)
            inspected += 1

            map_name = g.get("map_name") or g.get("mapName") or ""
            if not normalize_map(map_name).startswith(TARGET_MAP):
                continue

            details = client.get_json(f"{LEETIFY_BASE}/v2/matches/{game_id}") or g
            rating = deep_find(details, RATING_KEYS) or deep_find(g, RATING_KEYS)
            try:
                rating = int(rating) if rating is not None else None
            except (TypeError, ValueError):
                rating = None
            band = classify_band(rating)
            replay = deep_find(details, REPLAY_KEYS) or deep_find(g, REPLAY_KEYS)
            players = extract_players(details) or extract_players(g)

            cand = CandidateMatch(
                game_id=game_id,
                map_name=map_name,
                rating=rating,
                band=band,
                replay_url=replay,
                discovered_from=steam_id,
                data_source=["leetify_api_public"],
                players=players,
                played_at=str(g.get("finished_at") or g.get("played_at") or ""),
            )
            candidates.append(asdict(cand))
            flag = "OK" if band and replay else ("SEM_REPLAY" if band else "FORA_DA_FAIXA")
            print(f"  [{flag}] {game_id} rating={rating} band={band} replay={'sim' if replay else 'nao'} players={len(players)}")

            for p in players:
                if p not in visited_players:
                    queue.append((p, game_id))

        state["visited_players"] = sorted(visited_players)
        state["visited_matches"] = sorted(visited_matches)
        state["candidates"] = candidates
        save_state(state)
        print(f"[progresso] jogadores={players_done} partidas_inspecionadas={inspected} fila={len(queue)}")

    state["visited_players"] = sorted(visited_players)
    state["visited_matches"] = sorted(visited_matches)
    state["candidates"] = candidates
    state["client_stats"] = client.stats
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    approved = [c for c in candidates if c.get("band") and c.get("replay_url")]
    return {"state": state, "approved": approved}


# ------------------------------------------------------------------------------
# Download
# ------------------------------------------------------------------------------

def download_demo(replay_url: str, game_id: str, client: RateLimitedClient) -> Dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dem_path = RAW_DIR / f"{game_id}.dem"
    if dem_path.exists() and dem_path.stat().st_size > 0:
        return {"game_id": game_id, "status": "ALREADY_PRESENT", "path": str(dem_path), "bytes": dem_path.stat().st_size}

    compressed = RAW_DIR / f"{game_id}.dem.download"
    try:
        with client.session.get(replay_url, stream=True, timeout=60) as r:
            if r.status_code != 200:
                return {"game_id": game_id, "status": f"HTTP_{r.status_code}", "path": None, "bytes": 0}
            with open(compressed, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
    except Exception as e:
        if compressed.exists():
            compressed.unlink()
        return {"game_id": game_id, "status": f"ERROR_{type(e).__name__}", "path": None, "bytes": 0}

    head = b""
    with open(compressed, "rb") as f:
        head = f.read(4)

    try:
        if head[:3] == b"BZh":
            with bz2.open(compressed, "rb") as fin, open(dem_path, "wb") as fout:
                while True:
                    block = fin.read(1 << 20)
                    if not block:
                        break
                    fout.write(block)
        elif head[:2] == b"\x1f\x8b":
            with gzip.open(compressed, "rb") as fin, open(dem_path, "wb") as fout:
                while True:
                    block = fin.read(1 << 20)
                    if not block:
                        break
                    fout.write(block)
        else:
            # já descompactado
            os.replace(compressed, dem_path)
    except Exception as e:
        return {"game_id": game_id, "status": f"DECOMPRESS_ERROR_{type(e).__name__}", "path": None, "bytes": 0}
    finally:
        if compressed.exists():
            compressed.unlink()

    size = dem_path.stat().st_size if dem_path.exists() else 0
    return {"game_id": game_id, "status": "DOWNLOADED", "path": str(dem_path), "bytes": size}


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Crawler de demos amadoras de Mirage (Leetify)")
    ap.add_argument("--mode", choices=["discover", "download"], default="discover")
    ap.add_argument("--max-players", type=int, default=40)
    ap.add_argument("--max-matches", type=int, default=400)
    ap.add_argument("--per-player-limit", type=int, default=20)
    ap.add_argument("--min-interval", type=float, default=6.0)
    ap.add_argument("--max-downloads", type=int, default=50)
    ap.add_argument("--seeds", nargs="*", default=None)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get("LEETIFY_API_KEY")
    client = RateLimitedClient(api_key=api_key, min_interval=args.min_interval)
    print(f"[config] API key: {'SIM' if api_key else 'NAO (rate limit restrito)'}")

    if args.mode == "discover":
        result = crawl(
            seeds=args.seeds or DEFAULT_SEEDS,
            client=client,
            max_players=args.max_players,
            max_matches_inspected=args.max_matches,
            per_player_limit=args.per_player_limit,
        )
        manifest = {
            "schema": "csbot.amateur_mirage.discovery_manifest.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_map": TARGET_MAP,
            "rating_bands": RATING_BANDS,
            "client_stats": client.stats,
            "total_candidates": len(result["state"]["candidates"]),
            "approved_candidates": len(result["approved"]),
            "approved": result["approved"],
        }
        mpath = OUT_DIR / "discovery_manifest.json"
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\n[manifest] {mpath}")
        print(f"[resumo] candidatos={manifest['total_candidates']} aprovados={manifest['approved_candidates']}")
        return 0

    # mode == download
    mpath = OUT_DIR / "discovery_manifest.json"
    if not mpath.exists():
        print("[erro] rode --mode discover primeiro.")
        return 2
    with open(mpath, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = []
    for c in manifest.get("approved", []):
        if len([r for r in results if r["status"] == "DOWNLOADED"]) >= args.max_downloads:
            break
        print(f"[download] {c['game_id']} ({c['band']})")
        res = download_demo(c["replay_url"], c["game_id"], client)
        res["band"] = c.get("band")
        res["rating"] = c.get("rating")
        results.append(res)
        print(f"  -> {res['status']} ({res['bytes']} bytes)")

    dpath = OUT_DIR / "download_report.json"
    with open(dpath, "w", encoding="utf-8") as f:
        json.dump({"schema": "csbot.amateur_mirage.download_report.v1",
                   "generated_at": datetime.now(timezone.utc).isoformat(),
                   "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n[report] {dpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
