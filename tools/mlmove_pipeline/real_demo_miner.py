"""
Fase 6B: Minerador e Downloader Multi-Fonte de Demos Reais de CS2 para o Motor MLMove 16Hz.
Gera arquivos .dem reais em D:\CS2_MLMove_Pipeline\raw_demos\de_mirage\ com:
1. Controle de Estado e Anti-Duplicação (D:\CS2_MLMove_Pipeline\miner_state.json)
2. Validação Estrita de Header Source 2 (PBDEMS2) para proteger o demoparser2
3. Três Fontes de Dados:
   - Fonte 1: Repositórios Públicos HuggingFace / GitHub Datasets de CS2 (--source hf)
   - Fonte 2: Crawler HLTV / Faceit / URLs com Cloudscraper (--source hltv / --urls-file)
   - Fonte 3: Ingestão de Pasta Local + Gravações CSTV do Servidor (--source local)
4. Descompactação Seletiva: extrai apenas *mirage*.dem e remove o arquivo bruto comprimido (.rar/.zip/.zst)
"""

from __future__ import annotations
import argparse
import bz2
import hashlib
import json
import os
from pathlib import Path
import shutil
import site
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import zipfile

# Adiciona diretórios de pacotes de usuário ao sys.path para garantir acesso às bibliotecas
for extra_path in [
    site.getusersitepackages(),
    r"C:\Users\ricar\AppData\Local\Programs\Python\Python311\Lib\site-packages",
    r"C:\Users\ricar\AppData\Roaming\Python\Python311\site-packages",
]:
    if os.path.exists(extra_path) and extra_path not in sys.path:
        sys.path.append(extra_path)

import requests
from tqdm import tqdm

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import huggingface_hub
    from huggingface_hub import HfApi, hf_hub_download
except ImportError:
    huggingface_hub = None

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


# Constantes de Caminhos
DEFAULT_BASE_DIR = r"D:\CS2_MLMove_Pipeline"
DEFAULT_RAW_DEMOS = r"D:\CS2_MLMove_Pipeline\raw_demos\de_mirage"
DEFAULT_STATE_FILE = r"D:\CS2_MLMove_Pipeline\miner_state.json"
DEFAULT_URLS_FILE = r"D:\CS2_MLMove_Pipeline\demo_urls.txt"
DEFAULT_CSTV_DIR = r"H:\CS2_AI_Server\game\csgo"

SOURCE2_MAGIC_HEADER = b"PBDEMS2"
SOURCE1_MAGIC_HEADER = b"HL2DEMO"


# ==============================================================================
# 1. VALIDAÇÃO DE HEADER SOURCE 2 (PBDEMS2)
# ==============================================================================

def validate_cs2_demo_header(file_path: Path) -> Tuple[bool, str]:
    """
    Inspeciona os primeiros 8 bytes do arquivo .dem para garantir conformidade com o Source 2 do CS2.
    - Sucesso: Deve começar com b"PBDEMS2".
    - Rejeição 1: Começa com b"HL2DEMO" (CS:GO Source 1 antigo) -> Rejeita imediatamente para não quebrar o demoparser2!
    - Rejeição 2: Resposta HTML, arquivo corrompido, página de erro 403/404 ou vazio.
    """
    if not file_path.exists():
        return False, "Arquivo inexistente"
    
    file_size = file_path.stat().st_size
    if file_size < 1024:
        return False, f"Arquivo muito pequeno ({file_size} bytes - provavelmente erro HTTP/HTML)"

    try:
        with open(file_path, "rb") as f:
            header = f.read(8)

        if header.startswith(SOURCE2_MAGIC_HEADER):
            return True, "Source 2 CS2 (PBDEMS2)"
        elif header.startswith(SOURCE1_MAGIC_HEADER):
            return False, "CS:GO Source 1 (HL2DEMO) - Incompatível com o pipeline CS2"
        else:
            return False, f"Header desconhecido ({header[:8]!r}) - Arquivo inválido ou HTML"
    except Exception as exc:
        return False, f"Erro ao ler header: {exc}"


def compute_file_sha256(file_path: Path, sample_fast: bool = False) -> str:
    """Calcula o hash SHA256 do arquivo (completo ou amostrado para arquivos de 200MB+)."""
    h = hashlib.sha256()
    size = file_path.stat().st_size
    if sample_fast and size > 10 * 1024 * 1024:
        # Amostragem ultrarrápida: primeiros 2MB + miolo 2MB + últimos 2MB + tamanho
        with open(file_path, "rb") as f:
            h.update(f.read(2 * 1024 * 1024))
            f.seek(size // 2)
            h.update(f.read(2 * 1024 * 1024))
            f.seek(-2 * 1024 * 1024, os.SEEK_END)
            h.update(f.read(2 * 1024 * 1024))
        h.update(str(size).encode("ascii"))
        return f"fast_{h.hexdigest()}"

    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


# ==============================================================================
# 2. CONTROLE DE ESTADO (miner_state.json)
# ==============================================================================

class MinerState:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.downloaded_urls: Set[str] = set()
        self.processed_demo_hashes: Dict[str, Dict[str, Any]] = {}
        self.stats: Dict[str, Any] = {
            "total_downloaded": 0,
            "total_extracted_mirage": 0,
            "rejected_non_source2": 0,
            "last_updated": "",
        }
        self.load()

    def load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.downloaded_urls = set(data.get("downloaded_urls", []))
            self.processed_demo_hashes = data.get("processed_demo_hashes", {})
            self.stats = data.get("stats", self.stats)
        except Exception as exc:
            print(f"[MinerState] Aviso ao carregar estado de {self.state_path}: {exc}")

    def save(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.stats["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            data = {
                "downloaded_urls": sorted(list(self.downloaded_urls)),
                "processed_demo_hashes": self.processed_demo_hashes,
                "stats": self.stats,
            }
            # Gravação atômica via arquivo temporário
            tmp_path = self.state_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self.state_path)
        except Exception as exc:
            print(f"[MinerState] Erro ao salvar estado: {exc}")

    def is_url_done(self, url: str) -> bool:
        return url.strip() in self.downloaded_urls

    def mark_url_done(self, url: str) -> None:
        self.downloaded_urls.add(url.strip())
        self.stats["total_downloaded"] += 1
        self.save()

    def is_hash_processed(self, h: str) -> bool:
        return h in self.processed_demo_hashes

    def record_processed_demo(self, h: str, filename: str, source: str, size_mb: float) -> None:
        self.processed_demo_hashes[h] = {
            "filename": filename,
            "source": source,
            "size_mb": round(size_mb, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.stats["total_extracted_mirage"] += 1
        self.save()


# ==============================================================================
# 3. EXTRATOR INTELIGENTE DE PACOTES (*mirage*.dem)
# ==============================================================================

def extract_mirage_from_archive(
    archive_path: Path,
    dest_dir: Path,
    target_map_substring: str = "mirage",
    delete_archive_after: bool = True,
) -> List[Path]:
    """
    Descompacta SELETIVAMENTE apenas arquivos contendo 'mirage' e extensão '.dem'.
    Suporta .zip, .rar, .7z, .zst, .bz2.
    Descarta outros mapas do pacote (ex: de_inferno, de_anubis) para economizar disco NVMe.
    Apaga o pacote .rar/.zip/.zst após a extração se delete_archive_after for True.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted_files: List[Path] = []
    suffix = archive_path.suffix.lower()

    print(f"[Extrator] Inspecionando pacote: {archive_path.name} ({archive_path.stat().st_size // (1024*1024)} MB)...")

    try:
        # Caso A: ZIP
        if suffix == ".zip" or archive_path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member in zf.namelist():
                    lower_name = member.lower()
                    if lower_name.endswith(".dem") and target_map_substring in lower_name:
                        out_name = Path(member).name
                        target_file = dest_dir / out_name
                        print(f"  -> Extraindo Mirage: {out_name}...")
                        with zf.open(member) as src, open(target_file, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        extracted_files.append(target_file)
                    elif lower_name.endswith(".dem"):
                        print(f"  [Ignorado] Outro mapa descartado: {Path(member).name}")

        # Caso B: RAR
        elif suffix == ".rar":
            if rarfile is None:
                print("[Extrator] Biblioteca 'rarfile' não disponível para abrir .rar.")
            else:
                with rarfile.RarFile(str(archive_path)) as rf:
                    for member in rf.namelist():
                        lower_name = member.lower()
                        if lower_name.endswith(".dem") and target_map_substring in lower_name:
                            out_name = Path(member).name
                            target_file = dest_dir / out_name
                            print(f"  -> Extraindo Mirage (RAR): {out_name}...")
                            with rf.open(member) as src, open(target_file, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            extracted_files.append(target_file)
                        elif lower_name.endswith(".dem"):
                            print(f"  [Ignorado] Outro mapa descartado: {Path(member).name}")

        # Caso C: 7Z
        elif suffix in [".7z", ".cbz"]:
            if py7zr is None:
                print("[Extrator] Biblioteca 'py7zr' não disponível para abrir .7z.")
            else:
                with py7zr.SevenZipFile(str(archive_path), mode="r") as sz:
                    for name, bio in sz.readall().items():
                        lower_name = name.lower()
                        if lower_name.endswith(".dem") and target_map_substring in lower_name:
                            out_name = Path(name).name
                            target_file = dest_dir / out_name
                            print(f"  -> Extraindo Mirage (7z): {out_name}...")
                            with open(target_file, "wb") as f_out:
                                f_out.write(bio.read())
                            extracted_files.append(target_file)

        # Caso D: Zstandard (.zst)
        elif suffix == ".zst" or archive_path.name.lower().endswith(".dem.zst"):
            if zstd is None:
                print("[Extrator] Biblioteca 'zstandard' não disponível para abrir .zst.")
            else:
                out_name = archive_path.stem
                if not out_name.lower().endswith(".dem"):
                    out_name = f"{out_name}.dem"
                if target_map_substring in out_name.lower():
                    target_file = dest_dir / out_name
                    print(f"  -> Descomprimindo Zstandard: {out_name}...")
                    dctx = zstd.ZstdDecompressor()
                    with open(archive_path, "rb") as f_in, open(target_file, "wb") as f_out:
                        dctx.copy_stream(f_in, f_out)
                    extracted_files.append(target_file)
                else:
                    print(f"  [Ignorado] Arquivo Zstandard não é Mirage: {archive_path.name}")

        # Caso E: BZ2 (.bz2)
        elif suffix == ".bz2" or archive_path.name.lower().endswith(".dem.bz2"):
            out_name = archive_path.stem
            if not out_name.lower().endswith(".dem"):
                out_name = f"{out_name}.dem"
            if target_map_substring in out_name.lower():
                target_file = dest_dir / out_name
                print(f"  -> Descomprimindo BZ2: {out_name}...")
                with bz2.open(archive_path, "rb") as f_in, open(target_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                extracted_files.append(target_file)
            else:
                print(f"  [Ignorado] Arquivo BZ2 não é Mirage: {archive_path.name}")

    except Exception as exc:
        print(f"[Extrator] Erro ao extrair pacote {archive_path.name}: {exc}")

    # Remove o arquivo compactado bruto se solicitado
    if delete_archive_after:
        try:
            archive_path.unlink(missing_ok=True)
            print(f"  [Limpeza] Pacote compactado removido: {archive_path.name}")
        except Exception as exc:
            print(f"  [Limpeza] Aviso ao remover pacote: {exc}")

    return extracted_files


# ==============================================================================
# 4. DOWNLOADER EM STREAMING COM BARRA DE PROGRESSO E RETRY
# ==============================================================================

def download_file_stream(
    url: str,
    dest_path: Path,
    session: Optional[requests.Session] = None,
    max_retries: int = 3,
) -> bool:
    """Faz download de arquivo via streaming com barra de progresso tqdm e headers anti-bloqueio."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest_path.with_suffix(".part")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/octet-stream, application/zip, application/x-rar-compressed, */*",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    }

    sess = session or (cloudscraper.create_scraper() if cloudscraper else requests.Session())

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Download] ({attempt}/{max_retries}) Baixando: {url}")
            resp = sess.get(url, headers=headers, stream=True, timeout=60)
            if resp.status_code != 200:
                print(f"[Download] Falha HTTP {resp.status_code} na tentativa {attempt}.")
                time.sleep(2 * attempt)
                continue

            total_size = int(resp.headers.get("content-length", 0))
            with open(temp_dest, "wb") as f, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=dest_path.name,
                leave=False,
            ) as pbar:
                for chunk in resp.iter_content(chunk_size=128 * 1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            if temp_dest.exists() and temp_dest.stat().st_size > 1024:
                temp_dest.replace(dest_path)
                print(f"[Download] Concluído com sucesso: {dest_path.name} ({dest_path.stat().st_size // (1024*1024)} MB)")
                return True
        except Exception as exc:
            print(f"[Download] Erro na tentativa {attempt}: {exc}")
            time.sleep(2 * attempt)

    if temp_dest.exists():
        temp_dest.unlink(missing_ok=True)
    return False


# ==============================================================================
# 5. FONTE 1: HUGGINGFACE / GITHUB CS2 DATASETS (--source hf)
# ==============================================================================

def mine_from_huggingface(
    dest_dir: Path,
    state: MinerState,
    max_downloads: int = 10,
    repo_id_override: Optional[str] = None,
) -> int:
    """Busca e baixa arquivos de demos de CS2 do HuggingFace contendo partidas de Mirage."""
    if huggingface_hub is None:
        print("[Fonte HF] huggingface_hub não disponível.")
        return 0

    print(f"\n[Fonte 1 - HuggingFace] Buscando repositórios de CS2 no Hugging Face Hub...")
    api = HfApi()
    downloaded_count = 0

    # Lista de repositórios conhecidos com demos de CS2
    candidate_repos = []
    if repo_id_override:
        candidate_repos.append(repo_id_override)
    else:
        # Repositórios conhecidos de ML/CS2
        candidate_repos.extend([
            "david-durst/csknow-demos",
            "laiyer/cs2-demos",
            "cs2-analytics/competitive-demos",
            "ValveSoftware/cs2-match-demos",
        ])
        # Busca dinâmica por outros repositórios
        try:
            found_datasets = list(api.list_datasets(search="cs2", limit=15))
            for ds in found_datasets:
                if ds.id not in candidate_repos:
                    candidate_repos.append(ds.id)
        except Exception as exc:
            print(f"[Fonte HF] Busca dinâmica indisponível: {exc}")

    for repo_id in candidate_repos:
        if downloaded_count >= max_downloads:
            break
        try:
            print(f"[Fonte HF] Inspecionando dataset: {repo_id}...")
            files = list(api.list_repo_files(repo_id=repo_id, repo_type="dataset"))
            mirage_files = [
                f for f in files
                if "mirage" in f.lower() and (
                    f.lower().endswith(".dem") or
                    f.lower().endswith(".dem.zst") or
                    f.lower().endswith(".dem.bz2") or
                    f.lower().endswith(".zip")
                )
            ]

            print(f"  -> Encontrados {len(mirage_files)} arquivos de Mirage em {repo_id}.")
            for f_name in mirage_files:
                if downloaded_count >= max_downloads:
                    break
                url_key = f"hf://{repo_id}/{f_name}"
                if state.is_url_done(url_key):
                    continue

                local_path = dest_dir / Path(f_name).name
                print(f"[Fonte HF] Baixando {f_name} de {repo_id}...")
                try:
                    downloaded_file = hf_hub_download(
                        repo_id=repo_id,
                        filename=f_name,
                        repo_type="dataset",
                        local_dir=str(dest_dir),
                    )
                    state.mark_url_done(url_key)
                    downloaded_count += 1

                    # Se for compactado, descompacta imediatamente
                    p_file = Path(downloaded_file)
                    if p_file.suffix.lower() in [".zip", ".zst", ".bz2", ".rar", ".7z"]:
                        extract_mirage_from_archive(p_file, dest_dir, delete_archive_after=True)
                except Exception as exc:
                    print(f"[Fonte HF] Falha ao baixar {f_name}: {exc}")

        except Exception as exc:
            print(f"[Fonte HF] Repositório {repo_id} indisponível ou privado: {exc}")

    return downloaded_count


# ==============================================================================
# 6. FONTE 2: CRAWLER HLTV / FACEIT VIA CLOUDSCRAPER (--source hltv / --urls-file)
# ==============================================================================

def mine_from_urls_file(
    urls_file: Path,
    dest_dir: Path,
    state: MinerState,
    max_downloads: int = 15,
) -> int:
    """Lê lista de URLs de demos de CS2 de um arquivo de texto e baixa com cloudscraper."""
    if not urls_file.exists():
        # Cria arquivo template vazio com instruções claras
        urls_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(urls_file, "w", encoding="utf-8") as f:
                f.write("# Cole aqui URLs diretas de demos de CS2 (HLTV, Faceit, Datasets ou links HTTP)\n")
                f.write("# Exemplo:\n")
                f.write("# https://www.hltv.org/download/demo/XXXXX\n")
            print(f"[Fonte URLs] Criado template em {urls_file}. Adicione links lá para download automatizado.")
        except Exception:
            pass
        return 0

    with open(urls_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not lines:
        print(f"[Fonte URLs] Nenhuma URL ativa encontrada em {urls_file}.")
        return 0

    print(f"\n[Fonte 2 - URLs/HLTV] Processando {len(lines)} URLs do arquivo {urls_file.name}...")
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False}) if cloudscraper else requests.Session()
    success_count = 0

    for url in lines:
        if success_count >= max_downloads:
            break
        if state.is_url_done(url):
            continue

        # Nome derivado da URL ou hash
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        filename = f"demo_download_{url_hash}"
        if ".rar" in url.lower():
            filename += ".rar"
        elif ".zip" in url.lower():
            filename += ".zip"
        elif ".zst" in url.lower():
            filename += ".dem.zst"
        else:
            filename += ".dem"

        target_path = dest_dir / filename
        ok = download_file_stream(url, target_path, session=scraper)
        if ok:
            state.mark_url_done(url)
            success_count += 1
            # Se for pacote comprimido (.rar, .zip), descompacta apenas mirage e remove pacote
            if target_path.suffix.lower() in [".rar", ".zip", ".7z", ".zst", ".bz2"]:
                extract_mirage_from_archive(target_path, dest_dir, delete_archive_after=True)

    return success_count


# ==============================================================================
# 7. FONTE 3: INGESTÃO DE PASTA LOCAL + GRAVAÇÕES CSTV (--source local)
# ==============================================================================

def ingest_local_demos(
    raw_demos_dir: Path,
    cstv_server_dir: Path,
    state: MinerState,
) -> int:
    """
    Monitora a pasta de downloads e a pasta de gravações CSTV do servidor CS2.
    Descompacta qualquer arquivo .rar/.zip/.7z/.zst que o usuário colocou localmente
    e valida todos os arquivos .dem com o cabeçalho PBDEMS2.
    """
    raw_demos_dir.mkdir(parents=True, exist_ok=True)
    ingested_count = 0

    print(f"\n[Fonte 3 - Local & CSTV] Verificando gravações locais e pastas de ingestão...")

    # 1. Checa gravações CSTV do servidor (H:\CS2_AI_Server\game\csgo\csbot_*.dem)
    if cstv_server_dir.exists():
        cstv_demos = list(cstv_server_dir.glob("csbot_*.dem"))
        for cstv_path in cstv_demos:
            dest_dem = raw_demos_dir / cstv_path.name
            if not dest_dem.exists():
                print(f"[Fonte Local] Copiando gravação CSTV do servidor: {cstv_path.name} -> {dest_dem.name}...")
                try:
                    shutil.copy2(cstv_path, dest_dem)
                    ingested_count += 1
                except Exception as exc:
                    print(f"[Fonte Local] Erro ao copiar CSTV: {exc}")

    # 2. Descompacta pacotes que estejam soltos em raw_demos
    archive_patterns = ["*.zip", "*.rar", "*.7z", "*.zst", "*.bz2"]
    for pattern in archive_patterns:
        for archive_file in list(raw_demos_dir.glob(pattern)):
            print(f"[Fonte Local] Encontrado pacote compactado local: {archive_file.name}")
            extracted = extract_mirage_from_archive(archive_file, raw_demos_dir, delete_archive_after=True)
            ingested_count += len(extracted)

    # 3. Validação dos arquivos .dem existentes
    all_demos = sorted(raw_demos_dir.glob("*.dem"))
    valid_count = 0
    for dem_file in all_demos:
        is_valid, reason = validate_cs2_demo_header(dem_file)
        if not is_valid:
            print(f"[Header Check] REJEITADO: {dem_file.name} | Motivo: {reason}")
            # Move arquivo inválido ou corrompido para subpasta de quarentena
            quarantine_dir = raw_demos_dir / "quarantine_invalid"
            quarantine_dir.mkdir(exist_ok=True)
            try:
                dem_file.replace(quarantine_dir / dem_file.name)
            except Exception:
                pass
            state.stats["rejected_non_source2"] += 1
            state.save()
        else:
            valid_count += 1

    print(f"[Fonte Local] Demos válidas Source 2 (PBDEMS2) prontas para extração: {valid_count}")
    return ingested_count


# ==============================================================================
# 8. ORQUESTRADOR PRINCIPAL DO MINERADOR
# ==============================================================================

def run_miner(
    source: str = "all",
    base_dir: str = DEFAULT_BASE_DIR,
    urls_file_override: Optional[str] = None,
    max_demos: int = 25,
    map_name: str = "de_mirage",
) -> int:
    """Executa a coleta multi-fonte de demos de CS2."""
    base_path = Path(base_dir)
    raw_demos_path = base_path / "raw_demos" / map_name
    state_path = base_path / "miner_state.json"
    urls_path = Path(urls_file_override) if urls_file_override else (base_path / "demo_urls.txt")
    cstv_path = Path(DEFAULT_CSTV_DIR)

    # Se D:\ não estiver disponível, faz fallback seguro para o diretório de dados do projeto
    try:
        raw_demos_path.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        fallback_base = Path("D:/CS2_MLMove_Pipeline") if os.path.exists("D:/") else Path("tools/mlmove_pipeline/storage")
        print(f"[Minerador] Aviso: Destino {base_path} indisponível ({exc}). Usando fallback: {fallback_base}")
        base_path = fallback_base
        raw_demos_path = base_path / "raw_demos" / map_name
        state_path = base_path / "miner_state.json"
        urls_path = base_path / "demo_urls.txt"
        raw_demos_path.mkdir(parents=True, exist_ok=True)

    state = MinerState(state_path)

    print("=" * 65)
    print("      CsBot - Minerador Automatizado de Demos Reais de CS2")
    print("=" * 65)
    print(f"Diretório Alvo: {raw_demos_path}")
    print(f"Arquivo de Estado: {state_path}")
    print(f"Fonte Selecionada: {source.upper()} | Limite de Demos: {max_demos}")
    print(f"Histórico Atual: {len(state.downloaded_urls)} URLs baixadas, {len(state.processed_demo_hashes)} demos processadas.")
    print("=" * 65)

    total_added = 0

    # Executa as fontes solicitadas
    if source in ["all", "local"]:
        total_added += ingest_local_demos(raw_demos_path, cstv_path, state)

    if source in ["all", "urls", "hltv"]:
        total_added += mine_from_urls_file(urls_path, raw_demos_path, state, max_downloads=max_demos)

    if source in ["all", "hf", "huggingface"]:
        total_added += mine_from_huggingface(raw_demos_path, state, max_downloads=max_demos)

    print("\n" + "=" * 65)
    print(f"Minerador finalizado. Novas demos/pacotes adquiridos nesta rodada: {total_added}")
    print("=" * 65)
    return total_added


def main() -> None:
    parser = argparse.ArgumentParser(description="Minerador Multi-Fonte de Demos Reais de CS2 (MLMove)")
    parser.add_argument(
        "--source",
        type=str,
        default="all",
        choices=["all", "hf", "huggingface", "urls", "hltv", "local"],
        help="Fonte de demos a utilizar (default: all)",
    )
    parser.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Diretório raiz no NVMe (default: D:\\CS2_MLMove_Pipeline)")
    parser.add_argument("--urls-file", type=str, default=None, help="Caminho alternativo para arquivo de URLs")
    parser.add_argument("--max-demos", type=int, default=25, help="Quantidade máxima de novas demos a baixar neste lote (default: 25)")
    parser.add_argument("--map", type=str, default="de_mirage", help="Mapa competitivo alvo (default: de_mirage)")
    args = parser.parse_args()

    run_miner(
        source=args.source,
        base_dir=args.base_dir,
        urls_file_override=args.urls_file,
        max_demos=args.max_demos,
        map_name=args.map,
    )


if __name__ == "__main__":
    main()
