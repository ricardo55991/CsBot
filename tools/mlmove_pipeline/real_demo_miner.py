"""
CsBot MLMove Pipeline - Minerador Multi-Fonte 100% Autônomo de Demos Reais de CS2
Elimina a necessidade de colar links manualmente.
Fontes Ativas:
1. Hugging Face Hub Datasets Abertos (blanchon/opencs2_dataset_demo [366 demos de Mirage!], Vasy7777/cs2-demo-archive)
2. CSTV Ingestão Contínua do Servidor CS2 Local (H:\\CS2_AI_Server\\game\\csgo)
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from typing import Dict, List, Optional, Set
import zipfile

import requests
from tqdm import tqdm

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

try:
    from huggingface_hub import HfApi, hf_hub_download
except ImportError:
    HfApi = None
    hf_hub_download = None

try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import rarfile
except ImportError:
    rarfile = None

try:
    import zstandard as zstd
except ImportError:
    zstd = None

# Detecção dinâmica de disco (Prioridade Disco F:\\ com 520+ GB livres)
try:
    from contract_spec import DEFAULT_BASE_DIR
except ImportError:
    DEFAULT_BASE_DIR = os.environ.get(
        "CSBOT_PIPELINE_DIR",
        r"F:\CS2_MLMove_Pipeline" if os.path.exists(r"F:\CS2_MLMove_Pipeline") else r"D:\CS2_MLMove_Pipeline"
    )

DEFAULT_RAW_DEMOS = os.path.join(DEFAULT_BASE_DIR, "raw_demos", "de_mirage")
DEFAULT_STATE_FILE = os.path.join(DEFAULT_BASE_DIR, "miner_state.json")
DEFAULT_CSTV_DIR = r"H:\CS2_AI_Server\game\csgo"

SOURCE2_MAGIC_HEADER = b"PBDEMS2"


class MinerState:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.downloaded_urls: Set[str] = set()
        self.processed_demo_hashes: Set[str] = set()
        self.load()

    def load(self) -> None:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.downloaded_urls = set(data.get("downloaded_urls", []))
                    self.processed_demo_hashes = set(data.get("processed_demo_hashes", []))
            except Exception as exc:
                print(f"[MinerState] Aviso ao carregar estado: {exc}")

    def save(self) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "downloaded_urls": list(self.downloaded_urls),
                        "processed_demo_hashes": list(self.processed_demo_hashes),
                        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    f,
                    indent=2,
                )
        except Exception as exc:
            print(f"[MinerState] Aviso ao salvar estado: {exc}")

    def is_url_done(self, url: str) -> bool:
        return url in self.downloaded_urls

    def mark_url_done(self, url: str) -> None:
        self.downloaded_urls.add(url)
        self.save()

    def is_demo_hash_done(self, demo_hash: str) -> bool:
        return demo_hash in self.processed_demo_hashes

    def mark_demo_hash_done(self, demo_hash: str) -> None:
        self.processed_demo_hashes.add(demo_hash)
        self.save()


def validate_cs2_demo_header(file_path: Path) -> bool:
    if not file_path.exists() or file_path.stat().st_size < 1024:
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(7)
            return header == SOURCE2_MAGIC_HEADER
    except Exception:
        return False


def extract_zst_demo(zst_path: Path, dest_dir: Path) -> Optional[Path]:
    if zstd is None:
        return None
    out_name = zst_path.stem
    if not out_name.endswith(".dem"):
        out_name += ".dem"
    out_path = dest_dir / out_name

    try:
        dctx = zstd.ZstdDecompressor()
        with open(zst_path, "rb") as fin, open(out_path, "wb") as fout:
            dctx.copy_stream(fin, fout)
        if validate_cs2_demo_header(out_path):
            return out_path
    except Exception as exc:
        print(f"[ZSTD] Falha ao descompactar {zst_path.name}: {exc}")
        if out_path.exists():
            out_path.unlink(missing_ok=True)
    return None


def mine_from_huggingface_open_datasets(
    dest_dir: Path,
    state: MinerState,
    max_downloads: int = 25,
    map_name: str = "de_mirage",
) -> int:
    if HfApi is None:
        print("[Fonte HF] huggingface_hub não disponível.")
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    api = HfApi()
    downloaded = 0

    clean_map = map_name.replace("de_", "").lower()
    open_repos = [
        "blanchon/opencs2_dataset_demo",
        "Vasy7777/cs2-demo-archive",
    ]

    print(f"\n[Fonte Hugging Face Hub] Consultando datasets abertos da comunidade ({map_name})...")
    for repo_id in open_repos:
        if downloaded >= max_downloads:
            break
        try:
            files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
            # Filtro prioritário: partidas do mapa alvo (ex: mirage)
            mirage_files = [
                f for f in files 
                if clean_map in f.lower() and (f.endswith(".dem") or f.endswith(".zst") or f.endswith(".zip"))
            ]
            other_demo_files = [
                f for f in files 
                if (f.endswith(".dem") or f.endswith(".zst") or f.endswith(".zip")) and f not in mirage_files
            ]

            target_files = mirage_files + other_demo_files
            print(f"  -> Repositório {repo_id}: {len(mirage_files)} demos profissionais de {clean_map} localizadas (Total: {len(target_files)})")

            for rfile in target_files:
                if downloaded >= max_downloads:
                    break
                url_key = f"{repo_id}/{rfile}"
                if state.is_url_done(url_key):
                    continue

                filename_only = Path(rfile).name
                print(f"  -> Baixando demo CS2 ({downloaded + 1}/{max_downloads}): {filename_only}...")
                local_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=rfile,
                    repo_type="dataset",
                    local_dir=str(dest_dir),
                )
                p = Path(local_path)
                if p.suffix == ".zst":
                    extracted = extract_zst_demo(p, dest_dir)
                    p.unlink(missing_ok=True)
                elif p.suffix == ".zip":
                    try:
                        with zipfile.ZipFile(p, "r") as zf:
                            zf.extractall(dest_dir)
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass

                state.mark_url_done(url_key)
                downloaded += 1
        except Exception as exc:
            print(f"[Fonte HF] Repositório {repo_id}: {exc}")

    return downloaded


def ingest_local_demos(
    raw_demos_dir: Path,
    cstv_server_dir: Path,
    state: MinerState,
) -> int:
    raw_demos_dir.mkdir(parents=True, exist_ok=True)
    ingested_count = 0

    print(f"\n[Fonte CSTV & Local] Sincronizando partidas locais...")
    if cstv_server_dir.exists():
        for cstv_path in cstv_server_dir.glob("*.dem"):
            dest_dem = raw_demos_dir / cstv_path.name
            if not dest_dem.exists():
                try:
                    shutil.copy2(cstv_path, dest_dem)
                    if validate_cs2_demo_header(dest_dem):
                        ingested_count += 1
                except Exception:
                    pass

    return ingested_count


def run_miner(
    source: str = "all",
    base_dir: str = DEFAULT_BASE_DIR,
    max_demos: int = 25,
    map_name: str = "de_mirage",
    urls_file_override: Optional[str] = None,
) -> int:
    base_path = Path(base_dir)
    raw_demos_path = base_path / "raw_demos" / map_name
    state_path = base_path / "miner_state.json"
    cstv_path = Path(DEFAULT_CSTV_DIR)

    raw_demos_path.mkdir(parents=True, exist_ok=True)
    state = MinerState(state_path)

    total_added = 0
    total_added += ingest_local_demos(raw_demos_path, cstv_path, state)
    total_added += mine_from_huggingface_open_datasets(raw_demos_path, state, max_downloads=max_demos, map_name=map_name)

    print(f"\n[Minerador Autônomo] Total de novas demos profissionais obtidas: {total_added}")
    return total_added


def main() -> None:
    parser = argparse.ArgumentParser(description="Minerador 100% Autônomo de Demos Reais de CS2")
    parser.add_argument("--source", type=str, default="all", choices=["all", "hf", "local"])
    parser.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR)
    parser.add_argument("--max-demos", type=int, default=25)
    parser.add_argument("--map", type=str, default="de_mirage")
    args = parser.parse_args()

    run_miner(source=args.source, base_dir=args.base_dir, max_demos=args.max_demos, map_name=args.map)


if __name__ == "__main__":
    main()
