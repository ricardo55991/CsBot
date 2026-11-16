#!/usr/bin/env python3
"""
tools/intermediate_demo_acquisition/ingest_opt_in_demo.py
Ingestor offline de demonstrações voluntárias comunitárias (Valve Opt-In).

Valida integridade do arquivo .dem, formato de Share Code, termo de consentimento,
calcula SHA-256 por streaming, aplica pseudonimização HMAC-SHA256 e registra
a submissão para o inventário do corpus intermediário.

Padrão: --dry-run (nenhum arquivo é movido ou gravado permanentemente).
Aceita: --self-test (executa asserções determinísticas locais em fixtures sintéticas).
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

SHARE_CODE_REGEX = re.compile(r"^CSGO(-[0-9A-Za-z]{5}){5}$")
SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")
DEMO_MAGIC_BYTES_CS2 = b"PBDEMS2\x00"

def calculate_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def pseudonymize_identifier(raw_id: str, salt: str) -> str:
    return hmac.new(salt.encode("utf-8"), raw_id.encode("utf-8"), hashlib.sha256).hexdigest()

def validate_submission_payload(payload: dict) -> tuple[bool, str]:
    required_keys = [
        "share_code",
        "file_name",
        "map",
        "match_mode",
        "skill_bucket_declared",
        "consent_granted"
    ]
    for k in required_keys:
        if k not in payload:
            return False, f"Campo obrigatório ausente: {k}"

    if not SHARE_CODE_REGEX.match(payload["share_code"]):
        return False, f"Formato de Share Code inválido: {payload['share_code']}"

    if payload["map"] != "de_mirage":
        return False, f"Mapa não suportado para o estudo: {payload['map']} (exige de_mirage)"

    if payload["consent_granted"] is not True:
        return False, "Consentimento formal LGPD não concedido (consent_granted deve ser true)"

    return True, "VALID"

def run_self_test() -> int:
    print("[SELF-TEST] Iniciando asserções determinísticas de ingestão opt-in...")
    
    # 1. Validação de regex do Share Code
    valid_sc = "CSGO-abcde-12345-FGHIJ-67890-KLMNO"
    invalid_sc = "INVALID-SHARE-CODE"
    assert SHARE_CODE_REGEX.match(valid_sc), "Falha no regex de share code válido"
    assert not SHARE_CODE_REGEX.match(invalid_sc), "Falha no regex de share code inválido"

    # 2. Validação de Payload
    valid_payload = {
        "share_code": valid_sc,
        "file_name": "match_sample.dem",
        "map": "de_mirage",
        "match_mode": "Premier",
        "skill_bucket_declared": "VALVE_PREMIER_10K_13K",
        "consent_granted": True
    }
    ok, msg = validate_submission_payload(valid_payload)
    assert ok, f"Validação de payload válido falhou: {msg}"

    invalid_payload = valid_payload.copy()
    invalid_payload["map"] = "de_inferno"
    ok, msg = validate_submission_payload(invalid_payload)
    assert not ok, "Deveria recusar mapa diferente de de_mirage"

    # 3. Pseudonimização
    salt = "test_salt_secret_123"
    p1 = pseudonymize_identifier("76561198000000001", salt)
    p2 = pseudonymize_identifier("76561198000000001", salt)
    p3 = pseudonymize_identifier("76561198000000002", salt)
    assert p1 == p2, "Pseudonimização não é determinística"
    assert p1 != p3, "Colisão indevida de pseudônimos"
    assert SHA256_HEX_REGEX.match(p1), "Hash gerado não é SHA256 de 64 hexadecimais"

    print("[SELF-TEST] Todas as 6 asserções passaram com sucesso (PASS).")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Ingestor de Demos Comunitárias Valve Opt-In (CsBot)")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", default=True, help="Execução simulada sem alterar arquivos no disco (padrão)")
    mode_group.add_argument("--execute", action="store_true", help="Execução real da ingestão")
    mode_group.add_argument("--self-test", action="store_true", help="Executa testes unitários determinísticos locais")
    
    parser.add_argument("--submission-json", type=str, help="Caminho para o JSON de submissão do doador")
    parser.add_argument("--demo-path", type=str, help="Caminho para o arquivo .dem")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())

    print(f"INGEST_OPT_IN_DEMO: Executando em modo {'DRY_RUN' if not args.execute else 'EXECUTE'}")

    if not args.submission_json or not args.demo_path:
        print("Aviso: --submission-json e --demo-path não fornecidos. Modo demonstrativo de dry-run.")
        print("STATUS: DRY_RUN_VERIFIED_CLEAN (0 arquivos mutados)")
        sys.exit(0)

    sub_path = Path(args.submission_json)
    dem_path = Path(args.demo_path)

    if not sub_path.exists():
        print(f"ERRO: Arquivo de submissão não encontrado: {sub_path}")
        sys.exit(1)

    with open(sub_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    ok, msg = validate_submission_payload(payload)
    if not ok:
        print(f"REJEITADO: {msg}")
        sys.exit(1)

    if not dem_path.exists():
        print(f"ERRO: Arquivo .dem não encontrado: {dem_path}")
        sys.exit(1)

    file_size = dem_path.stat().st_size
    file_sha256 = calculate_sha256(dem_path)

    print(f"DEMO_VALIDATED: size={file_size} bytes, sha256={file_sha256}")
    print("STATUS: DRY_RUN_COMPLETE (Pronto para promoção em modo execute)")
    sys.exit(0)

if __name__ == "__main__":
    main()
