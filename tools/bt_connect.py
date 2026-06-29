"""
FACOM DX.TSCANPB — Session persistante : handshake + séquence commandes + écoute
"""

import socket
import time
from pathlib import Path

MAC     = "00:07:80:87:34:1E"
CHANNEL = 3
LOG_DIR = Path(__file__).parent / "bt_capture"
LOG_DIR.mkdir(exist_ok=True)

JPEG_SOI = bytes([0xFF, 0xD8])
JPEG_EOI = bytes([0xFF, 0xD9])


def recv_timeout(sock, timeout=2.0):
    sock.settimeout(0.15)
    buf = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = sock.recv(4096)
            if chunk:
                buf.extend(chunk)
                deadline = time.time() + 0.5
        except socket.timeout:
            pass
    return bytes(buf)


def save_jpegs(data, prefix):
    count = 0
    pos = 0
    while True:
        start = data.find(JPEG_SOI, pos)
        if start == -1:
            break
        end = data.find(JPEG_EOI, start + 2)
        if end != -1:
            count += 1
            fname = LOG_DIR / f"{prefix}_{count:04d}.jpg"
            fname.write_bytes(data[start:end + 2])
            print(f"  *** JPEG #{count} → {fname.name} ***")
            pos = end + 2
        else:
            break
    return count


def send_cmd(sock, label, cmd):
    print(f"  TX [{label:20s}] {cmd.hex(' ').upper()}")
    sock.send(cmd)
    time.sleep(0.3)
    resp = recv_timeout(sock, 1.5)
    if resp:
        print(f"  RX [{label:20s}] {resp.hex(' ').upper()}  ({len(resp)} octets)")
    else:
        print(f"  RX [{label:20s}] (aucune réponse)")
    return resp


def main():
    print("=" * 60)
    print("  FACOM — Session persistante")
    print("=" * 60)
    input("\nSCANDIAG fermé ? Entrée pour démarrer…\n")

    print(f"Connexion {MAC} canal {CHANNEL}…")
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(10)
    sock.connect((MAC, CHANNEL))
    print("CONNECTÉ !\n")

    # ── Handshake ────────────────────────────────────────────────
    print("[HANDSHAKE]")
    hello = recv_timeout(sock, 3.0)
    print(f"  Hello  : {hello.hex(' ').upper()}")
    ack = bytes([0x00]) + hello[1:]
    sock.send(ack)
    ready = recv_timeout(sock, 2.0)
    print(f"  Ready  : {ready.hex(' ').upper()}")
    print()

    # ── Séquence de commandes (connexion maintenue) ───────────────
    print("[SÉQUENCE COMMANDES]")
    # Construction du paquet : 00 00 07 10 00 01 [CMD]
    def pkt(cmd_byte):
        return bytes([0x00, 0x00, 0x07, 0x10, 0x00, 0x01, cmd_byte])

    cmds = [
        ("init 0x01",    pkt(0x01)),
        ("init 0x02",    pkt(0x02)),
        ("init 0x03",    pkt(0x03)),
        ("init 0x04",    pkt(0x04)),
        ("init 0x05",    pkt(0x05)),
        ("init 0x06",    pkt(0x06)),
        ("init 0x07",    pkt(0x07)),
        ("init 0x08",    pkt(0x08)),
        ("start 0x10",   pkt(0x10)),
        ("start 0x20",   pkt(0x20)),
        ("start 0x40",   pkt(0x40)),
    ]

    all_responses = bytearray()
    for label, cmd in cmds:
        resp = send_cmd(sock, label, cmd)
        if resp:
            all_responses.extend(resp)
        time.sleep(0.5)

    save_jpegs(bytes(all_responses), "cmds")

    # ── Écoute passive longue ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("CONNEXION MAINTENUE — APPUIE SUR LE BOUTON DE L'OUTIL !")
    print("Écoute 90 secondes…")
    print("=" * 60 + "\n")

    raw_log  = open(LOG_DIR / "session.bin", "wb")
    all_data = bytearray()
    t0 = time.time()
    sock.settimeout(0.3)

    while time.time() - t0 < 90:
        try:
            chunk = sock.recv(4096)
            if chunk:
                all_data.extend(chunk)
                raw_log.write(chunk)
                raw_log.flush()
                ts   = time.strftime("%H:%M:%S")
                prev = chunk[:32].hex(' ').upper()
                print(f"[{ts}] {len(chunk):5d} octets | {prev}")
                save_jpegs(bytes(all_data), "live")
        except socket.timeout:
            elapsed = int(time.time() - t0)
            if elapsed % 10 == 0:
                print(f"  …attente {elapsed}s — appuie sur le bouton !", end="\r")
        except Exception as e:
            print(f"\n[ERREUR] {e}")
            break

    raw_log.close()
    sock.close()

    total = LOG_DIR / "session.bin"
    if all_data:
        total.write_bytes(bytes(all_data))
        print(f"\n[DUMP] {len(all_data)} octets capturés → {total}")
    else:
        print("\n[INFO] Aucune donnée reçue pendant l'écoute.")


if __name__ == "__main__":
    main()
