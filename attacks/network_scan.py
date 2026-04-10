#!/usr/bin/env python3
# Attack 1: Network Scan using ICMP and TCP SYN
# Run from any host e.g: internet
# Usage: python3 network_scan.py

from scapy.all import *
import ipaddress

def icmp_scan(subnet):
    print(f"\n[*] ICMP scan on {subnet}")
    for ip in ipaddress.IPv4Network(subnet).hosts():
        ip = str(ip)
        pkt = IP(dst=ip)/ICMP()
        reply = sr1(pkt, timeout=1, verbose=0)
        if reply:
            print(f"  [+] {ip} is UP (ICMP)")

def tcp_syn_scan(subnet, ports=[21, 22, 80, 5353]):
    print(f"\n[*] TCP SYN scan on {subnet} ports {ports}")
    for ip in ipaddress.IPv4Network(subnet).hosts():
        ip = str(ip)
        for port in ports:
            pkt = IP(dst=ip)/TCP(dport=port, flags="S")
            reply = sr1(pkt, timeout=1, verbose=0)
            if reply and reply.haslayer(TCP):
                if reply[TCP].flags == "SA":
                    print(f"  [+] {ip}:{port} is OPEN")
                elif reply[TCP].flags == "RA":
                    print(f"  [-] {ip}:{port} is CLOSED")

if __name__ == "__main__":
    # Scan DMZ subnet
    icmp_scan("10.12.0.0/24")
    tcp_syn_scan("10.12.0.0/24")
    
    # Scan workstation subnet
    icmp_scan("10.1.0.0/24")
    tcp_syn_scan("10.1.0.0/24")
