"""
Fase 6B (Camada 2 - Parte 1): Gerenciador de Coleta e Descompactação de Demos em Lotes no Disco D:\
Armazenamento estrito em `F:\CS2_MLMove_Pipeline\raw_demos\<map>\`.

Recursos:
1. Download em lotes (`--batch-size 50 --map de_mirage`) a partir de listas de URLs ou manifestos públicos.
2. Ingestão automática de arquivos compactados (`.zip`, `.zst`, `.bz2`, `.gz`, `.rar`, `.tar`) ou pastas locais.
3. Coleta direta das demos CSTV gravadas pelo nosso próprio servidor dedicado (`H:\CS2_AI_Server\game\csgo\*.dem`).
"""

from __future__ import annotations
import argparse
import bz2
import gzip
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import List

import requests
import zstandard as zstd
from tqdm import tqdm

from contract_spec import RAW_DEMOS_DIR_D


CSTV_SERVER_CSGO_DIR = Path(r"H:\CS2_AI_Server\game\csgo")


def ensure_map_raw_dir(map_name: str) -> Path:
    target = Path(RAW_DEMOS_DIR_D) / map_name
    target.mkdir(parents=True, exist_ok=True)
    return target


def decompress_single_file(archive_path: Path, dest_dir: Path, delete_archive: bool = False) -> List[Path]:
    """Descompacta .zst, .bz2, .gz, .zip, .tar ou .rar diretamente para dest_dir."""
    extracted_demos: List[Path] = []
    suffix = archive_path.suffix.lower()

    try:
        if suffix == ".dem":
            if archive_path.parent.resolve() != dest_dir.resolve():
                out_path = dest_dir / archive_path.name
                shutil.copy2(archive_path, out_path)
                extracted_demos.append(out_path)
            else:
                extracted_demos.append(archive_path)
            return extracted_demos

        if suffix == ".zst":
            out_name = archive_path.stem
            if not out_name.endswith(".dem"):
                out_name += ".dem"
            out_path = dest_dir / out_name
            dctx = zstd.ZstdDecompressor()
            with open(archive_path, "rb") as ifh, open(out_path, "wb") as ofh:
                dctx.copy_stream(ifh, ofh)
            extracted_demos.append(out_path)

        elif suffix == ".bz2":
            out_name = archive_path.stem
            if not out_name.endswith(".dem"):
                out_name += ".dem"
            out_path = dest_dir / out_name
            with bz2.BZ2File(archive_path, "rb") as ifh, open(out_path, "wb") as ofh:
                shutil.copyfileobj(ifh, ofh)
            extracted_demos.append(out_path)

        elif suffix == ".gz" and not archive_path.name.endswith(".tar.gz"):
            out_name = archive_path.stem
            if not out_name.endswith(".dem"):
                out_name += ".dem"
            out_path = dest_dir / out_name
            with gzip.open(archive_path, "rb") as ifh, open(out_path, "wb") as ofh:
                shutil.copyfileobj(ifh, ofh)
            extracted_demos.append(out_path)

        elif suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member in zf.namelist():
                    if member.lower().endswith(".dem"):
                        filename = Path(member).name
                        out_path = dest_dir / filename
                        with zf.open(member) as src, open(out_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        extracted_demos.append(out_path)

        elif suffix in (".tar", ".tgz") or archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:*") as tf:
                for member in tf.getmembers():
                    if member.isfile() and member.name.lower().endswith(".dem"):
                        filename = Path(member.name).name
                        out_path = dest_dir / filename
                        src = tf.extractfile(member)
                        if src is not None:
                            with src, open(out_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            extracted_demos.append(out_path)

        elif suffix == ".rar":
            # Tenta usar tar.exe nativo do Windows 11 (bsdtar suporta .rar!) ou 7z
            before_files = set(dest_dir.glob("*.dem"))
            cmd = ["tar.exe", "-xf", str(archive_path), "-C", str(dest_dir)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                seven_zip = shutil.which("7z") or r"C:\Program Files\7-Zip\7z.exe"
                if Path(str(seven_zip)).exists():
                    subprocess.run([str(seven_zip), "e", str(archive_path), f"-o{dest_dir}", "*.dem", "-r", "-y"], check=False)
            after_files = set(dest_dir.glob("*.dem"))
            extracted_demos.extend(list(after_files - before_files))

        if delete_archive and extracted_demos and archive_path.exists() and suffix != ".dem":
            archive_path.unlink(missing_ok=True)

    except Exception as exc:
        print(f"[demo_collector] Aviso ao descompactar {archive_path.name}: {exc}")

    return extracted_demos


def ingest_directory(source_dir: Path, map_name: str, batch_size: int, delete_archives: bool = False) -> List[Path]:
    """Varre uma pasta em busca de .dem, .zip, .rar, .zst, .bz2 e prepara lote em D:\\CS2_MLMove_Pipeline\\raw_demos\\<map>."""
    dest_dir = ensure_map_raw_dir(map_name)
    if not source_dir.exists():
        return []

    collected: List[Path] = []
    patterns = ("*.dem", "*.zst", "*.bz2", "*.gz", "*.zip", "*.rar", "*.tar")
    candidates: List[Path] = []
    for pat in patterns:
        candidates.extend(source_dir.rglob(pat))

    for item in candidates:
        if len(collected) >= batch_size:
            break
        demos = decompress_single_file(item, dest_dir, delete_archive=delete_archives)
        collected.extend(demos)

    return collected[:batch_size]


def ingest_cstv_server_demos(map_name: str = "de_mirage") -> List[Path]:
    """Importa demos CSTV gravadas pelo nosso servidor em H:\\CS2_AI_Server\\game\\csgo\\."""
    dest_dir = ensure_map_raw_dir(map_name)
    if not CSTV_SERVER_CSGO_DIR.exists():
        return []

    imported: List[Path] = []
    for dem in CSTV_SERVER_CSGO_DIR.glob("*.dem"):
        if map_name.lower() in dem.name.lower() or "csbot" in dem.name.lower():
            if dem.stat().st_size > 64 * 1024:
                target = dest_dir / dem.name
                shutil.copy2(dem, target)
                imported.append(target)
                print(f"[demo_collector] Demo CSTV importada para D:\\: {target.name} ({dem.stat().st_size // 1024} KB)")
    return imported


def download_urls_batch(
    urls: List[str],
    map_name: str = "de_mirage",
    batch_size: int = 50,
    delete_archive_after_unpack: bool = True,
) -> List[Path]:
    """Baixa um lote de até `batch_size` URLs de demos (.dem / .zst / .rar / .zip) para o disco D:\\."""
    dest_dir = ensure_map_raw_dir(map_name)
    ready_demos: List[Path] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CsBot-MLMove-Research/1.0"
    }

    for url in urls[:batch_size]:
        url = url.strip()
        if not url or url.startswith("#"):
            continue

        filename = url.split("?")[0].rstrip("/").split("/")[-1]
        if not any(filename.endswith(ext) for ext in (".dem", ".zst", ".bz2", ".zip", ".rar", ".gz")):
            filename += ".dem.zst"

        download_path = dest_dir / filename
        try:
            print(f"[demo_collector] Baixando {url} -> {download_path}...")
            with requests.get(url, headers=headers, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                with open(download_path, "wb") as f, tqdm(
                    total=total, unit="B", unit_scale=True, desc=filename, leave=False
                ) as bar:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))

            extracted = decompress_single_file(download_path, dest_dir, delete_archive=delete_archive_after_unpack)
            ready_demos.extend(extracted)
        except Exception as exc:
            print(f"[demo_collector] Aviso ao baixar {url}: {exc}")

    return ready_demos


def main() -> None:
    parser = argparse.ArgumentParser(description="Coletor em Lotes de Demos CS2 (Disco F:\\)")
    parser.add_argument("--map", type=str, default="de_mirage", help="Mapa alvo (default: de_mirage)")
    parser.add_argument("--batch-size", type=int, default=50, help="Tamanho máximo do lote de demos")
    parser.add_argument("--ingest-dir", type=str, default="", help="Pasta local com arquivos .dem/.rar/.zip/.zst")
    parser.add_argument("--urls-file", type=str, default="", help="Arquivo .txt com URLs de demos para download")
    parser.add_argument("--url", type=str, action="append", default=[], help="URL individual de demo para baixar")
    parser.add_argument("--ingest-cstv", action="store_true", help="Importa demos gravadas pelo CSTV em H:\\CS2_AI_Server")
    parser.add_argument("--delete-after-extract", action="store_true", help="Remove arquivos compactados após extrair .dem")
    args = parser.parse_args()

    dest_dir = ensure_map_raw_dir(args.map)
    print(f"[demo_collector] Pasta de lote no NVMe D:\\: {dest_dir}")

    collected: List[Path] = []

    if args.ingest_cstv:
        collected.extend(ingest_cstv_server_demos(args.map))

    if args.ingest_dir:
        collected.extend(
            ingest_directory(Path(args.ingest_dir), args.map, args.batch_size, delete_archives=args.delete_after_extract)
        )

    # Descompacta qualquer arquivo compactado já colocado manualmente em F:\CS2_MLMove_Pipeline\raw_demos\<map>
    collected.extend(ingest_directory(dest_dir, args.map, args.batch_size, delete_archives=args.delete_after_extract))

    urls: List[str] = list(args.url)
    if args.urls_file and Path(args.urls_file).exists():
        urls.extend(Path(args.urls_file).read_text(encoding="utf-8").splitlines())

    if urls:
        collected.extend(
            download_urls_batch(
                urls,
                map_name=args.map,
                batch_size=args.batch_size,
                delete_archive_after_unpack=args.delete_after_extract,
            )
        )

    all_ready = sorted(dest_dir.glob("*.dem"))
    print(f"[demo_collector] Total de demos .dem prontas em {dest_dir}: {len(all_ready)}")


if __name__ == "__main__":
    main()
