#!/usr/bin/env python3
# Simple UDP reflector simulates an amplification server
# Run this ON the ntp server


import socket

HOST = "0.0.0.0"
PORT = 12345

def start_reflector():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[*] UDP Reflector listening on port {PORT}")
    print(f"[*] Will send large replies to any request")
    
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[*] Got request from {addr} - sending amplified reply")
        # Send large reply - amplification!
        large_reply = b"X" * 1000  # 1000 bytes vs small request
        sock.sendto(large_reply, addr)

if __name__ == "__main__":
    start_reflector()
