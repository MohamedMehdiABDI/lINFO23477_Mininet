# LINFO2347 - Network Attacks Project

## Group Members
- Student 1: [Your Name]
- Student 2: [Partner Name]

## Overview
This project implements a secure enterprise network topology using mininet, with basic firewall protection and 4 network attacks with their corresponding protections.

---

## Network Topology

The topology mimics a typical enterprise network with three zones:

```
Let's do this systematically. First let me sync all files to the project folder, then create the README, then the PPT.
Step 1 — Sync all files on Terminal 2:
bashcp ~/LINFO2347/attacks/* ~/project/attacks/
cp ~/LINFO2347/protections/* ~/project/protections/
cp ~/LINFO2347/firewall.sh ~/project/
Step 2 — Create the README:
bashnano ~/project/README.md
Paste this:
markdown# LINFO2347 - Network Attacks Project

## Group Members
- Student 1: [Your Name]
- Student 2: [Partner Name]

## Overview
This project implements a secure enterprise network topology using mininet, with basic firewall protection and 4 network attacks with their corresponding protections.

---

## Network Topology

The topology mimics a typical enterprise network with three zones:

```
internet -- r2 -- s2 -- DMZ servers (10.12.0.x)
                   |
                  r1 -- s1 -- workstations (10.1.0.x)
```

### Hosts
| Host | IP | Service |
|------|----|---------|
| ws2 | 10.1.0.2 | Workstation |
| ws3 | 10.1.0.3 | Workstation |
| http | 10.12.0.10 | Apache2 HTTP (port 80) |
| dns | 10.12.0.20 | dnsmasq DNS (port 5353) |
| ntp | 10.12.0.30 | OpenNTPD NTP (port 123) |
| ftp | 10.12.0.40 | vsftpd FTP (port 21) |
| internet | 10.2.0.2 | External host |
| r1 | 10.1.0.1 / 10.12.0.1 | Internal router |
| r2 | 10.2.0.1 / 10.12.0.2 | Gateway router |

---

## How to Run

### 1. Start the topology
```bash
sudo mn -c
sudo -E python3 ~/LINFO2347/topo.py 16582510
```

### 2. Apply basic enterprise firewall
```bash
sudo bash ~/LINFO2347/firewall.sh
```

### 3. Start Apache on http server
```bash
sudo mnexec -a $(pgrep -f "mininet:http") bash -c 'pkill -9 apache2; sleep 1; apache2ctl -D FOREGROUND &'
```

---

## Basic Enterprise Network Protection

### Policy
The basic firewall implements the following security policies:

| Zone | Policy |
|------|--------|
| Workstations | Can ping and initiate connections to anyone |
| DMZ Servers | Cannot initiate connections, can only respond |
| Internet | Can only reach DMZ servers, cannot reach workstations |

### Implementation
Rules are applied using nftables on:
- **Each DMZ server** (http, dns, ntp, ftp): output chain with `policy drop`, only allowing `established,related` traffic
- **r2**: forward chain blocking new connections and pings from internet to workstation subnet `10.1.0.0/24`

### Verification
```bash
# Should FAIL - DMZ cannot initiate
mininet> http ping ws2 -c 2

# Should FAIL - internet cannot reach workstations  
mininet> internet ping ws2 -c 2

# Should WORK - internet can reach DMZ
mininet> internet ping http -c 2

# Should WORK - workstations can reach anyone
mininet> ws2 ping http -c 2
```

---

## Attack 1 — Network Scan

### Script
`attacks/network_scan.py`

### How to run
```bash
# Without protection
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/network_scan.py

# Apply protection
sudo bash ~/LINFO2347/protections/protect_scan.sh

# With protection
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/network_scan.py
```

### Attack Logic
The attacker runs from the `internet` host and performs two types of scans:

1. **ICMP Scan**: Sends ICMP echo requests to every IP in the subnet to discover which hosts are alive
2. **TCP SYN Scan**: Sends TCP SYN packets to common ports (21, 22, 80, 5353) on each host. If the host replies with SYN-ACK the port is open, if it replies with RST the port is closed, if there is no reply the port is filtered

**Before protection**, the scan reveals:
- `10.12.0.10:22` OPEN (SSH on http server)
- `10.12.0.20:5353` OPEN (DNS)
- `10.12.0.30:22` OPEN (SSH on ntp server)
- `10.12.0.40:21` OPEN (FTP)
- `10.12.0.40:22` OPEN (SSH on ftp server)

This gives the attacker a complete map of the network and its services.

### Protection Logic
`protections/protect_scan.sh` — applied on **r2**

Two nftables rules:

**Rule 1 — Rate limit ICMP:**
```
iifname "r2-eth0" icmp type echo-request limit rate over 3/second drop
```
A legitimate user sends at most 1-2 pings per second. A scanner sends dozens per second — this throttles the scan significantly.

**Rule 2 — Block TCP SYN to sensitive ports:**
```
iifname "r2-eth0" ip protocol tcp tcp flags syn tcp dport != { 80, 21 } drop
```
Only ports 80 (HTTP) and 21 (FTP) are publicly accessible services. All other ports (SSH, DNS) are hidden from the internet.

**After protection**, the scan only reveals:
- `10.12.0.10:80` OPEN (HTTP — intentionally public)
- `10.12.0.40:21` OPEN (FTP — intentionally public)

SSH and DNS are completely hidden, reducing the attack surface significantly.

---

## Attack 2 — FTP Brute Force

### Script
`attacks/ftp_bruteforce.py`

### How to run
```bash
# Without protection
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/ftp_bruteforce.py

# Apply protection
sudo bash ~/LINFO2347/protections/protect_ftp_bruteforce.sh

# With protection
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/ftp_bruteforce.py
```

### Attack Logic
The attacker runs from the `internet` host and tries all combinations of usernames and passwords against the FTP server on port 21.

Each attempt opens a **new TCP connection**:
1. TCP SYN → connect to port 21
2. Send `USER username`
3. Send `PASS password`
4. Check response: `230` = success, `530` = failure
5. Close connection and try next combination

Without protection, the attack successfully finds `mininet:mininet` credentials.

### Protection Logic
`protections/protect_ftp_bruteforce.sh` — applied on **ftp server**

Uses an nftables **meter** to track new connections per source IP:

```
tcp dport 21 ct state new meter ftp_limit 
{ ip saddr limit rate 3/minute burst 3 packets } accept
tcp dport 21 ct state new drop
```

The meter allows maximum 3 new TCP connections per minute per source IP. After 3 attempts the attacker must wait 1 minute before trying again.

**The math:**
- Our wordlist: 35 combinations
- Without protection: found in ~17 seconds
- With protection: 3 attempts/minute = 11 minutes for 35 passwords
- Real wordlist (100,000 passwords): ~23 days

The rule applies to **any** source IP exceeding the rate — not a specific attacker IP, satisfying the assignment requirement.

---

## Attack 3 — ARP Cache Poisoning

### Script
`attacks/arp_poison.py`

### How to run
```bash
# Check ws2 ARP cache before attack
sudo mnexec -a $(pgrep -f "mininet:ws2") arp -n

# Without protection - run from ws3
sudo mnexec -a $(pgrep -f "mininet:ws3") python3 ~/LINFO2347/attacks/arp_poison.py

# Check ws2 ARP cache during attack
sudo mnexec -a $(pgrep -f "mininet:ws2") arp -n

# Apply protection
sudo bash ~/LINFO2347/protections/protect_arp_poison.sh

# Flush poisoned cache
sudo mnexec -a $(pgrep -f "mininet:ws2") ip neigh flush all

# Run attack again - should be blocked
sudo mnexec -a $(pgrep -f "mininet:ws3") python3 ~/LINFO2347/attacks/arp_poison.py
```

### Attack Logic
The attacker runs from `ws3` and poisons `ws2`'s ARP cache:

1. `ws3` sends **fake ARP reply** to `ws2`: "I am the gateway `10.1.0.1`, my MAC is `ws3_MAC`"
2. `ws2` updates its ARP cache with the fake entry
3. All of `ws2`'s traffic destined for the gateway now goes to `ws3` instead
4. `ws3` becomes a **Man in the Middle** — it can intercept, read, or modify all of `ws2`'s traffic

**Before attack:**
```
10.1.0.1    ae:df:24:09:d4:7a   ← r1's real MAC
```
**During attack:**
```
10.1.0.1    d2:0f:ec:f5:e3:5d   ← ws3's MAC (POISONED!)
```

### Protection Logic
`protections/protect_arp_poison.sh` — applied on **ws2 and ws3**

Uses nftables ARP table filtering:

```
arp operation reply arp saddr ip 10.1.0.1 
arp saddr ether != GATEWAY_MAC drop
```

This rule drops any ARP reply that claims to be the gateway (`10.1.0.1`) but comes from a MAC address that is not the real gateway MAC. Any host can still send legitimate ARP replies — only fake ones claiming to be the gateway are dropped.

**After protection:**
```
10.1.0.1    GONE (fake ARP replies rejected)
```

---

## Attack 4 — Reflected DDoS (UDP Amplification)

### Scripts
- `attacks/udp_reflector.py` — simulates a vulnerable UDP server
- `attacks/reflected_ddos.py` — the attack script

### How to run
```bash
# Start the reflector on ntp server
sudo mnexec -a $(pgrep -f "mininet:ntp") python3 ~/LINFO2347/attacks/udp_reflector.py &

# Monitor victim BEFORE protection
sudo mnexec -a $(pgrep -f "mininet:http") tcpdump -i http-eth0 udp port 12345 -c 10 -v

# Run the attack
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/reflected_ddos.py

# Apply protection
sudo bash ~/LINFO2347/protections/protect_reflected_ddos.sh

# Run attack again then check counter
sudo mnexec -a $(pgrep -f "mininet:internet") python3 ~/LINFO2347/attacks/reflected_ddos.py
sudo mnexec -a $(pgrep -f "mininet:http") nft list ruleset
```

### Attack Logic
This is a **Reflected DDoS with amplification**:

1. Attacker spoofs source IP as victim (`10.12.0.10`) and sends small `GET` request (3 bytes) to the reflector
2. Reflector thinks the victim sent the request and replies with 1000 bytes
3. Victim receives 1000 byte replies it never requested
4. Attacker is hidden — traffic appears to come from the reflector

**Amplification factor:**
- Attacker sends: 200 × 3 bytes = **600 bytes**
- Victim receives: 200 × 1000 bytes = **200,000 bytes**
- **Amplification factor = 333x**

In real attacks, public DNS or NTP servers are used as reflectors, making the attack extremely difficult to stop since traffic comes from legitimate servers.

### Protection Logic
`protections/protect_reflected_ddos.sh` — applied on **http server**

```
ip protocol udp udp sport 12345 counter drop
```

Drops all unsolicited UDP packets from the reflector port. Since the victim never initiated any connection to port 12345, all incoming UDP from that port is by definition unsolicited amplification traffic.

**Proof of protection:**
```
counter packets 200 bytes 205600 drop
```
All 200 amplified packets (205,600 bytes) were dropped before reaching any application.

---

## File Structure

```
LINFO2347/
├── topo.py                          # Mininet topology
├── firewall.sh                      # Basic enterprise protection
├── attacks/
│   ├── network_scan.py             # Attack 1: Network scan
│   ├── ftp_bruteforce.py           # Attack 2: FTP brute force
│   ├── arp_poison.py               # Attack 3: ARP cache poisoning
│   ├── udp_reflector.py            # Attack 4: UDP reflector server
│   └── reflected_ddos.py           # Attack 4: Reflected DDoS
└── protections/
    ├── protect_scan.sh             # Protection against network scan
    ├── protect_ftp_bruteforce.sh   # Protection against FTP brute force
    ├── protect_arp_poison.sh       # Protection against ARP poisoning
    └── protect_reflected_ddos.sh   # Protection against reflected DDoS
```
