# LINFO2347 — project2

This project builds a small enterprise network in Mininet (two subnets: a DMZ and a workstation LAN, connected via a router to a simulated internet host). It demonstrates 5 attack/defense pairs: network scan, FTP brute force, ARP poisoning, botnet HTTP flood, and reflected UDP DDoS.

## Start the topology

Run on the VM host (from this directory):

```bash
cd /project2UCL/lINFO23477_Mininet
sudo mn -c
sudo -E python3 topo.py YOURNOMA   
```

This opens the Mininet CLI.
- Run **attacks** from the Mininet CLI (prefix with the host name, e.g. `internet ...`, `ws3 ...`).
- Run **defenses** from the VM host in a separate terminal (scripts use `mnexec` + `pgrep`).

Tip: scapy-based attacks usually require root. If you get permission errors, run `sudo python3 ...` inside the Mininet host.

---

## 1) Apply the initial enterprise firewall

`firewall.sh` is the **basic enterprise network protection** and must be applied first.

Policy enforced:
- Workstations (ws2, ws3) can initiate connections (incl. ping) to any host.
- DMZ servers (http, dns, ntp, ftp) cannot initiate new outbound connections (only reply).
- Internet can only initiate connections toward DMZ (not toward workstations).

Apply it (VM host, while topology is running):

```bash
sudo bash firewall.sh
```

**Verify the firewall policy (Mininet CLI):**

```bash
# Internet cannot reach workstations — should fail/timeout
internet ping -c 2 10.1.0.10

# Workstations can still reach DMZ — should succeed
ws2 ping -c 2 10.12.0.10
ws2 curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.12.0.10/
```

```bash
# Inspect r2 forward rules (VM host)
sudo bash -c "mnexec -a $(pgrep -f 'mininet:r2') nft list ruleset"
```



---

## 2) 5 Attack/Defense pairs


### Network scan

**Attack:** discover live hosts and open ports. The script probes both subnets (DMZ `10.12.0.0/24` and workstation `10.1.0.0/24`) using ICMP echo-requests to find hosts that respond, and TCP SYN packets to common ports (FTP/SSH/HTTP/DNS) to infer open services (SYN-ACK means open).

**Execute (Mininet CLI):**
```bash
internet python3 attacks/network_scan.py
```

**Expected output:** The script prints each host that replied to ICMP and each port that returned a SYN-ACK, revealing the live DMZ hosts and their open services.

---

**Defense:** reduce scan visibility at the perimeter router. On `r2`, we rate-limit ICMP echo-requests arriving from the internet side and drop TCP SYN packets targeting non-public ports, so scanners cannot easily map the DMZ and cannot probe internal services.

**Execute (VM host):**
```bash
sudo bash protections/protect_scan.sh
```

**Verify (Mininet CLI + VM host):**
```bash
# Re-run scan — ICMP is rate-limited and non-public SYNs are blocked
internet python3 attacks/network_scan.py

# Confirm r2 forward rules (VM host)
sudo bash -c "mnexec -a $(pgrep -f 'mininet:r2') nft list ruleset"
```

> Expected: significantly fewer host replies (ICMP rate-capped at 3/s), and port probes to anything other than 80 and 21 get no response.

---

### FTP brute force

**Attack:** try many username/password combinations against the FTP server (`10.12.0.40:21`). The script repeatedly opens TCP connections and sends `USER`/`PASS` commands; if the server returns code `230`, the login succeeded.

**Execute (Mininet CLI):**
```bash
internet python3 attacks/ftp_bruteforce.py
```

**Expected output:** Rapid connection attempts printed one per line; a `230 Login successful` line appears if a correct credential is found.

---

**Defense:** slow brute force using connection rate limiting on the FTP server. We accept only a small number of new connections per minute per source IP (using nftables `meter`), then drop additional new attempts. This keeps normal FTP usage working while making password guessing impractically slow.

**Execute (VM host):**
```bash
sudo bash protections/protect_ftp_bruteforce.sh
```

**Verify (Mininet CLI + VM host):**
```bash
# Re-run brute force — first 3 attempts connect, then new connections are dropped
internet python3 attacks/ftp_bruteforce.py

# Inspect ftp server input rules (VM host)
sudo bash -c "mnexec -a $(pgrep -f 'mininet:ftp') nft list ruleset"
```

> Expected: the first 3 connection attempts from the same IP succeed; all subsequent attempts within the same minute are silently dropped.

---

### ARP cache poisoning

**Attack:** poison the victim's ARP cache on the local LAN. The attacker (ws3) sends forged ARP replies to the victim (ws2) claiming that the gateway IP (`10.1.0.1`) is bound to the attacker's MAC address. This can enable traffic redirection / MITM on a flat LAN.

**Execute (Mininet CLI — check cache before, then run attack):**
```bash
# Check ws2's ARP cache before the attack — gateway IP maps to the real router MAC
ws2 arp -n

# Run the attack from ws3
ws3 python3 attacks/arp_poison.py

# Check ws2's ARP cache again — gateway IP now maps to ws3's MAC
ws2 arp -n
```

**Expected output:** After the attack, `ws2 arp -n` shows the gateway IP (`10.1.0.1`) pointing to ws3's MAC instead of the router's MAC.

---

**Defense:** prevent gateway spoofing by filtering ARP at the workstation. We drop ARP replies that claim to be from the gateway IP unless the sender MAC matches the legitimate gateway MAC (MAC pinning). This blocks the poisoning packets without breaking normal ARP.

**Execute (VM host):**
```bash
sudo bash protections/protect_arp_poison.sh
```

**Verify (Mininet CLI):**
```bash
# Flush ws2's ARP cache and re-run the attack
ws2 ip neigh flush all
ws3 python3 attacks/arp_poison.py

# Gateway MAC on ws2 should still be the real router MAC
ws2 arp -n
```

> Expected: `ws2 arp -n` continues to show the legitimate gateway MAC — forged ARP replies are silently dropped.

---

### Reflected DDoS (UDP amplification)

**Attack:** reflected/amplified flooding via source-IP spoofing. The attacker spoofs the victim IP and sends small UDP requests to a reflector; the reflector answers with much larger UDP replies to the victim, amplifying the traffic that hits the victim.

**Execute (prep, Mininet CLI — start reflector on ntp):**
```bash
ntp python3 attacks/udp_reflector.py &
```

**Execute (Mininet CLI):**
```bash
internet python3 attacks/reflected_ddos.py
```

**Expected output:** The HTTP server (`10.12.0.10`) is flooded with UDP packets sourced from the reflector on port 12345. The `reflected_ddos.py` script prints the number of amplified packets sent.

---

**Defense:** block the amplification traffic at the victim. On the HTTP server, we drop the unsolicited UDP replies coming from the reflector port used by this demo (`12345`) so the amplified traffic does not reach the application.

**Execute (VM host):**
```bash
sudo bash protections/protect_reflected_ddos.sh
```

**Verify (Mininet CLI + VM host):**
```bash
# Re-run the attack
ntp python3 attacks/udp_reflector.py &
internet python3 attacks/reflected_ddos.py

# Drop counter on http server — the packets field should be incrementing (VM host)
sudo bash -c "mnexec -a $(pgrep -f 'mininet:http') nft list ruleset"

# HTTP service is still reachable despite the flood
ws2 curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.12.0.10/
```

> Expected: the nftables counter shows UDP packets being dropped; the HTTP service still returns `HTTP 200`.

---

### Botnet HTTP flood (C&C + bots)

**Attack:** distributed application-layer DoS using multiple compromised hosts (bots). A C&C server runs on the internet host and waits for bots to connect. Once enough bots are connected, it commands them to repeatedly connect to the HTTP server (`10.12.0.10:80`) and send HTTP requests, increasing load with traffic from multiple sources.

**Execute (Mininet CLI):**

1. Start the bots on the workstation hosts (bots will keep looking for C&C every 2 seconds):
```bash
ws2 python3 attacks/bot.py &
ws3 python3 attacks/bot.py &
```

2. Start the C&C server (waits 10 s for bots to connect, then sends the ATTACK command):
```bash
internet python3 attacks/botnet_cnc.py &
```

**Expected output:** After ~10 s the C&C sends the flood command; the HTTP server starts receiving a high volume of connections from both ws2 and ws3.

Verify the attack is running:
```bash
ws2 jobs
ws3 jobs
internet jobs
```

Useful cleanup commands:
```bash
ws2 pkill -f bot.py
ws3 pkill -f bot.py
internet pkill -f botnet_cnc.py
```

---

**Defense:** rate-limit abusive clients at the DMZ servers. The defense installs nftables rules on DMZ servers to reject excessive new connections per source IP (HTTP/FTP/DNS/NTP service ports). This preserves normal traffic while throttling floods.

**Execute (VM host):**
```bash
sudo bash protections/protect_botnet.sh
```

**Verify (Mininet CLI + VM host):**
```bash
# Bots will start seeing most requests rejected 
ws2 jobs
ws3 jobs
```

> Expected: `ws2 curl` returns `HTTP 200`; bots see an increasing number of rejected connections while legitimate single requests succeed.

---

## 3) End-to-end verification — normal operations after all protections

With all protections applied, confirm that legitimate traffic still flows correctly:

**From the Mininet CLI:**
```bash
# All DMZ services reachable from workstations
ws2 curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.12.0.10/
ws2 ping -c 2 10.12.0.10    # HTTP server
ws2 ping -c 2 10.12.0.20    # DNS server
ws2 ping -c 2 10.12.0.30    # NTP server
ws2 ping -c 2 10.12.0.40    # FTP server

# Workstations can reach the internet
ws2 ping -c 2 10.2.0.1

# Internet can still reach DMZ public services (HTTP on port 80)
internet curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.12.0.10/

# Internet cannot reach workstations — should fail/timeout
internet ping -c 2 10.1.0.10
```

> Expected: all DMZ pings and the HTTP curl return successfully; the internet→workstation ping fails — the enterprise security policy is intact and services remain operational.
