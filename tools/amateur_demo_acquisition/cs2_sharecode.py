"""Decodificador de share code do CS2/CS:GO e gerador de URLs de replay da Valve.

Um share code tem o formato `CSGO-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`.
Cada caractere pertence a um alfabeto de 57 simbolos; os 25 simbolos
(sem os dashes e sem o prefixo `CSGO`) formam um inteiro em base 57,
lido em ordem reversa. Os 18 bytes resultantes sao:

    byte 0        : versao do formato (esperado 1 para matchmaking/CS2)
    bytes 1..8    : match_id   (uint64 little-endian)
    bytes 9..16   : outcome_id (uint64 little-endian)

O CDN de replays da Valve segue o padrao:

    http://replay{cluster}.valve.net/730/{match_id}_{outcome_id}.dem.bz2

Referencia do algoritmo: implementacao publica `csgo-sharecode` (akiver).

Nenhuma chamada de rede e' feita por este modulo: apenas decodificacao
deterministica e montagem de URLs candidatas.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789"
DICTIONARY_INDEX = {c: i for i, c in enumerate(DICTIONARY)}

# A base e' o tamanho do alfabeto (54), nao 57. Prova: 54**25 ~= 2**143.9,
# que cabe exatamente nos 18 bytes (144 bits) do payload. Usar 57 produzia
# byte de versao invalido (39) e IDs inexistentes no CDN.
BASE = len(DICTIONARY)  # 54

SHARE_CODE_LEN = 25
PAYLOAD_BYTES = 18


class ShareCodeError(ValueError):
    """Share code malformado."""


def normalize(share_code: str) -> str:
    """Remove prefixo e separadores, preservando o case."""
    sc = (share_code or "").strip()
    if sc.upper().startswith("CSGO"):
        sc = sc[4:]
    return sc.replace("-", "")


def decode(share_code: str) -> Tuple[int, int, int]:
    """Decodifica um share code.

    Retorna:
        (version, match_id, outcome_id)
    """
    body = normalize(share_code)
    if len(body) != SHARE_CODE_LEN:
        raise ShareCodeError(
            f"share code deve ter {SHARE_CODE_LEN} simbolos uteis; recebido {len(body)}"
        )

    total = 0
    for ch in reversed(body):
        idx = DICTIONARY_INDEX.get(ch)
        if idx is None:
            raise ShareCodeError(f"simbolo invalido no share code: {ch!r}")
        total = total * BASE + idx

    # 18 bytes = 36 digitos hexadecimais
    hexstr = format(total, "x").rjust(PAYLOAD_BYTES * 2, "0")
    if len(hexstr) > PAYLOAD_BYTES * 2:
        raise ShareCodeError("share code produz payload maior que o esperado")
    raw = bytes.fromhex(hexstr)

    version = raw[0]
    match_id = int.from_bytes(raw[1:9], "little", signed=False)
    outcome_id = int.from_bytes(raw[9:17], "little", signed=False)
    return version, match_id, outcome_id


def replay_urls(match_id: int, outcome_id: int, clusters: Optional[List[int]] = None,
                scheme: str = "http") -> List[Tuple[int, str]]:
    """URLs candidatas de replay, uma por cluster Valve."""
    if clusters is None:
        clusters = list(range(1, 21))
    return [
        (c, f"{scheme}://replay{c}.valve.net/730/{match_id}_{outcome_id}.dem.bz2")
        for c in clusters
    ]


def from_share_code(share_code: str) -> dict:
    """Atalho: share code -> dicionario com ids e URLs candidatas."""
    version, match_id, outcome_id = decode(share_code)
    return {
        "share_code": share_code,
        "version": version,
        "match_id": str(match_id),
        "outcome_id": str(outcome_id),
        "replay_candidates": replay_urls(match_id, outcome_id),
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("uso: python cs2_sharecode.py CSGO-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx [--json]")
        raise SystemExit(2)
    info = from_share_code(sys.argv[1])
    if "--json" in sys.argv:
        info["replay_candidates"] = info["replay_candidates"][:3]
        print(json.dumps(info, indent=2))
    else:
        print(f"share_code  : {info['share_code']}")
        print(f"version     : {info['version']}")
        print(f"match_id    : {info['match_id']}")
        print(f"outcome_id  : {info['outcome_id']}")
        print("replay cand.: primeiras 3")
        for c, u in info["replay_candidates"][:3]:
            print(f"  cluster {c:>2}: {u}")
