import argparse
import socket
import struct


def parse_header(packet: bytes):
    if len(packet) < 12:
        return None
    return struct.unpack("!HHHHHH", packet[:12])


def parse_qname(packet: bytes, offset: int = 12):
    labels = []
    i = offset
    while i < len(packet):
        l = packet[i]
        if l == 0:
            return ".".join(labels), i + 1
        i += 1
        labels.append(packet[i : i + l].decode("ascii", errors="replace"))
        i += l
    return "<invalid>", i


def forward_query(data: bytes, upstream_host: str, upstream_port: int) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(data, (upstream_host, upstream_port))
        resp, _ = sock.recvfrom(4096)
        return resp
    finally:
        sock.close()


def serve(port: int, upstream: str):
    host, p = upstream.split(":")
    upstream_port = int(p)

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("0.0.0.0", port))
    print(f"dns forwarder listening on udp :{port} -> {upstream}")

    while True:
        data, addr = server.recvfrom(4096)
        header = parse_header(data)
        if not header:
            continue
        qname, _ = parse_qname(data)
        qid = header[0]
        print(f"query id={qid} from={addr[0]}:{addr[1]} name={qname}")

        try:
            response = forward_query(data, host, upstream_port)
            server.sendto(response, addr)
        except Exception:
            continue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5353)
    parser.add_argument("--upstream", default="8.8.8.8:53")
    args = parser.parse_args()
    serve(args.port, args.upstream)


if __name__ == "__main__":
    main()
