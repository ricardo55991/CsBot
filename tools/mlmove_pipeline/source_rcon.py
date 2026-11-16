import socket
import struct
import time

class SourceRcon:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.host, self.port))
        # Auth packet
        self._send(3, self.password)
        # Receive auth response
        resp_id, resp_type, resp_body = self._recv()
        if resp_id == -1:
            raise ConnectionError("RCON authentication failed")
        return True

    def _send(self, packet_type, body):
        payload = struct.pack("<ii", 1, packet_type) + body.encode("utf-8") + b"\x00\x00"
        packet = struct.pack("<i", len(payload)) + payload
        self.sock.sendall(packet)

    def _recv(self):
        hdr = self.sock.recv(4)
        if not hdr:
            return -1, -1, ""
        size = struct.unpack("<i", hdr)[0]
        data = self.sock.recv(size)
        resp_id, resp_type = struct.unpack("<ii", data[:8])
        body = data[8:-2].decode("utf-8", errors="ignore")
        return resp_id, resp_type, body

    def command(self, cmd):
        self._send(2, cmd)
        try:
            _, _, body = self._recv()
            return body
        except Exception:
            return ""

    def close(self):
        if self.sock:
            self.sock.close()

print("SourceRcon class defined successfully")
