#!/usr/bin/env python3
import argparse
import socket
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 29000
DEFAULT_HANDSHAKE_HEX = "5646435300d40000000d000000"
PRNT_TEXT_OFFSET = 40


def clean_hex(value: str) -> str:
    return "".join(value.split())


def build_cmnd_packet(command: str) -> bytes:
    cmd = command.encode("ascii") + b"\x00"
    packet_len = 12 + len(cmd)

    if packet_len > 255:
        raise ValueError("command is too long for the one-byte CMND size field")

    return (
        b"CMND"
        + bytes.fromhex("00d40000")
        + bytes([0x00, packet_len, 0x00, 0x00])
        + cmd
    )


def format_ascii(data: bytes) -> str:
    if not data:
        return "(none)"

    chars = []
    for byte in data:
        if byte == 0x0a:
            chars.append("\\n")
        elif byte == 0x0d:
            chars.append("\\r")
        elif byte == 0x09:
            chars.append("\\t")
        elif 0x20 <= byte <= 0x7e:
            chars.append(chr(byte))
        else:
            chars.append(f"\\x{byte:02x}")

    return "".join(chars)


def split_vconsole_frames(data: bytes) -> list[tuple[str, bytes]]:
    frames = []
    offset = 0
    signatures = (b"PRNT", b"CMND", b"VFCS")

    while offset < len(data):
        matches = [data.find(signature, offset) for signature in signatures]
        matches = [match for match in matches if match != -1]
        if not matches:
            break

        start = min(matches)
        if start + 10 > len(data):
            break

        frame_len = data[start + 9]
        if frame_len < 12:
            offset = start + 1
            continue

        end = start + frame_len
        if end > len(data):
            break

        frame_type = data[start : start + 4].decode("ascii", errors="replace")
        frames.append((frame_type, data[start:end]))
        offset = end

    return frames


def extract_prnt_text(frame: bytes) -> str:
    if len(frame) <= PRNT_TEXT_OFFSET:
        return ""

    text_bytes = frame[PRNT_TEXT_OFFSET:].split(b"\x00", 1)[0]
    return text_bytes.decode("utf-8", errors="replace").rstrip("\r\n")


def format_response(data: bytes, mode: str) -> str:
    if not data:
        return "(none)"

    if mode == "hex":
        return data.hex()

    if mode == "ascii":
        return format_ascii(data)

    prnt_texts = [
        extract_prnt_text(frame)
        for frame_type, frame in split_vconsole_frames(data)
        if frame_type == "PRNT"
    ]
    prnt_texts = [text for text in prnt_texts if text]

    if prnt_texts:
        return "\n".join(prnt_texts)

    return format_ascii(data)


def recv_available(sock: socket.socket, timeout: float) -> bytes:
    chunks = []
    sock.settimeout(timeout)

    while True:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break

        if not chunk:
            break
        chunks.append(chunk)

    return b"".join(chunks)


def send_tcp(
    payload: bytes,
    host: str,
    port: int,
    handshake: bytes | None,
    wait_after_handshake: float,
    wait_after_command: float,
) -> tuple[bytes, bytes]:
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        flushed_response = b""
        if handshake:
            sock.sendall(handshake)
            if wait_after_handshake > 0:
                flushed_response = recv_available(sock, wait_after_handshake)

        sock.sendall(payload)
        time.sleep(wait_after_command)

        return flushed_response, recv_available(sock, 0.5)

    return flushed_response, b""


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a CS2 VConsole CMND packet over TCP")
    parser.add_argument(
        "command",
        nargs="?",
        help='console command to send, for example: "echo 12345"',
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--hex", dest="hex_data", help="raw hex payload to send")
    parser.add_argument("--recv", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--recv-hex", action="store_true", help="print response bytes as hex")
    parser.add_argument(
        "--recv-ascii",
        action="store_true",
        help="print response bytes as escaped ASCII",
    )
    parser.add_argument("--show-payload", action="store_true", help="print the CMND payload being sent")
    parser.add_argument(
        "--show-flush",
        action="store_true",
        help="print data received and discarded after the VFCS handshake",
    )
    parser.add_argument(
        "--no-handshake",
        action="store_true",
        help="do not send the VFCS application handshake before CMND",
    )
    parser.add_argument(
        "--handshake-hex",
        default=DEFAULT_HANDSHAKE_HEX,
        help="raw hex payload for the VFCS application handshake",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=2.0,
        help="seconds to wait after the VFCS handshake before sending CMND",
    )
    parser.add_argument(
        "--post-wait",
        type=float,
        default=0.2,
        help="seconds to keep the TCP connection open after sending CMND",
    )
    args, unknown_args = parser.parse_known_args()

    if unknown_args:
        if (
            len(unknown_args) == 1
            and args.command is None
            and unknown_args[0].startswith("-")
            and not unknown_args[0].startswith("--")
        ):
            args.command = unknown_args[0]
        else:
            parser.error(f"unrecognized arguments: {' '.join(unknown_args)}")

    if args.recv_hex and args.recv_ascii:
        parser.error("--recv-hex and --recv-ascii cannot be used together")

    if args.hex_data:
        payload = bytes.fromhex(clean_hex(args.hex_data))
    else:
        if not args.command:
            parser.error('the following arguments are required: command, for example: "echo 12345"')
        payload = build_cmnd_packet(args.command)

    if args.show_payload:
        print(f"payload ({len(payload)} bytes): {payload.hex()}")

    handshake = None if args.no_handshake else bytes.fromhex(clean_hex(args.handshake_hex))

    flushed_response, response = send_tcp(
        payload,
        args.host,
        args.port,
        handshake,
        args.wait,
        args.post_wait,
    )

    response_mode = "text"
    if args.recv_hex:
        response_mode = "hex"
    elif args.recv_ascii:
        response_mode = "ascii"

    if args.show_flush and flushed_response:
        formatted = format_response(flushed_response, response_mode)
        print(f"flushed after handshake ({len(flushed_response)} bytes): {formatted}")

    formatted = format_response(response, response_mode)
    print(f"response ({len(response)} bytes): {formatted}")


if __name__ == "__main__":
    main()
