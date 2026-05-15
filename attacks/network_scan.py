#!/usr/bin/env python3
# Attack 1: Network Scan using ICMP and TCP SYN
# Run from any host e.g: internet

from scapy.all import *
import ipaddress

def icmp_scan(subnet):
    print(f"\n[*] ICMP scan on {subnet}")
    hosts = [str(ip) for ip in ipaddress.IPv4Network(subnet).hosts()]
    # Send all pings at once to speed up the scan
    ans, unans = sr(IP(dst=hosts)/ICMP(), timeout=2, verbose=0)
    for sent, received in ans:
        print(f"  [+] {received.src} is UP (ICMP)")
    print(f"  [*] {len(ans)} hosts up, {len(unans)} not responding")

def tcp_syn_scan(target, ports=[21, 22, 80, 123, 443, 5353, 8080]):
    print(f"\n[*] TCP SYN scan on {target} ports {ports}")
    ans, unans = sr(IP(dst=target)/TCP(dport=ports, flags="S"), timeout=2, verbose=0)
    for sent, received in ans:
        if received.haslayer(TCP):
            if received[TCP].flags == "SA":
                print(f"  [+] {received.src}:{received[TCP].sport} is OPEN")
            elif received[TCP].flags == "RA":
                print(f"  [-] {received.src}:{received[TCP].sport} is CLOSED")
    print(f"  [*] {len(ans)} responses, {len(unans)} filtered/no response")

if __name__ == "__main__":
    print("=" * 50)
    print("[*] Network Scanner")
    print("=" * 50)

    # Scan DMZ subnet
    icmp_scan("10.12.0.0/24")
    tcp_syn_scan("10.12.0.0/24")

    # Scan workstation subnet
    icmp_scan("10.1.0.0/24")
    tcp_syn_scan("10.1.0.0/24")

    print("\n" + "=" * 50)
    print("[*] Scan complete!")
    print("=" * 50)