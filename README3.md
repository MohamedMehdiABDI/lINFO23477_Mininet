# LINFO2347 — project2

This project builds a small enterprise network in Mininet (two subnets: a DMZ and a workstation LAN, connected via a router to a simulated internet host). It demonstrates 5 attack/defense pairs: network scan, FTP brute force, ARP poisoning, botnet HTTP flood, and reflected UDP DDoS.

## Start the topology

Run on the VM host (from this directory):

```bash
sudo -E python3 topo.py YOURNOMA   # YOURNOMA = your student NOMA number
```

This opens the Mininet CLI.
- Run **attacks** from the Mininet CLI (prefix with the host name, e.g. `internet ...`, `ws3 ...`).
- Run **defenses** from the VM host in a separate terminal (scripts use `mnexec` + `pgrep`).

Tip: scapy-based attacks usually require root. If you get permission errors, run `sudo python3 ...` inside the Mininet host.

## 1) Apply the initial enterprise firewall
`firewall.sh` is the **basic enterprise network protection** and must be applied first.

Policy enforced:
- Workstations (ws2, ws3) can initiate connections (incl. ping) to any host.
- DMZ servers (http, dns, ntp, ftp) cannot initiate new outbound connections (only reply).
- Internet can only initiate connections toward DMZ (not toward workstations).

Apply it (VM host, while topology is running):

```bash
bash firewall.sh
```

Note: after this, `pingall` is not expected to succeed.

---

## 2) 5 Attack/Defense pairs

### Network scan
**Attack:** discover live hosts and open ports. The script probes both subnets (DMZ `10.12.0.0/24` and workstation `10.1.0.0/24`) using ICMP echo-requests to find hosts that respond, and TCP SYN packets to common ports (FTP/SSH/HTTP/DNS) to infer open services (SYN-ACK means open).

**Execute (Mininet CLI):**
```bash
internet python3 attacks/network_scan.py
```

**Defense:** reduce scan visibility at the perimeter router. On `r2`, we rate-limit ICMP echo-requests arriving from the internet side and drop TCP SYN packets targeting non-public ports, so scanners cannot easily map the DMZ and cannot probe internal services.

**Execute (VM host):**
```bash
bash protections/protect_scan.sh
```
Verify: re-run the scan; ICMP is rate-limited and unexpected SYNs are blocked.

### FTP brute force
**Attack:** try many username/password combinations against the FTP server (`10.12.0.40:21`). The script repeatedly opens TCP connections and sends `USER`/`PASS` commands; if the server returns code `230`, the login succeeded.

**Execute (Mininet CLI):**
```bash
internet python3 attacks/ftp_bruteforce.py
```

**Defense:** slow brute force using connection rate limiting on the FTP server. We accept only a small number of new connections per minute per source IP (using nftables `meter`), then drop additional new attempts. This keeps normal FTP usage working while making password guessing impractically slow.

**Execute (VM host):**
```bash
bash protections/protect_ftp_bruteforce.sh
```
Verify: re-run; after a few tries, new connections get dropped (rate limiting).

### ARP cache poisoning
**Attack:** poison the victim's ARP cache on the local LAN. The attacker (ws3) sends forged ARP replies to the victim (ws2) claiming that the gateway IP (`10.1.0.1`) is bound to the attacker's MAC address. This can enable traffic redirection / MITM on a flat LAN.

**Execute (Mininet CLI — from ws3 targeting ws2):**
```bash
ws3 python3 attacks/arp_poison.py
```

**Defense:** prevent gateway spoofing by filtering ARP at the workstation. We drop ARP replies that claim to be from the gateway IP unless the sender MAC matches the legitimate gateway MAC (MAC pinning). This blocks the poisoning packets without breaking normal ARP.

**Execute (VM host):**
```bash
bash protections/protect_arp_poison.sh
```
Verify: re-run; ARP replies spoofing the gateway MAC are dropped.

### Botnet HTTP flood (C&C + bots)
**Attack:** distributed application-layer DoS using multiple compromised hosts (bots). A C&C server runs on the internet host and waits for bots to connect. Once enough bots are connected, it commands them to repeatedly connect to the HTTP server (`10.12.0.10:80`) and send HTTP requests, increasing load with traffic from multiple sources.

**Execute (Mininet CLI):**
1) Start the C&C on the internet host it waits for bots 10 seconds, then launches automatically
(must start the bot attacks under 10 seconds):
```bash
internet python3 attacks/botnet_cnc.py
```
2) Start bots on both workstations:
```bash
ws2 python3 attacks/bot.py &
ws3 python3 attacks/bot.py &
```
Useful cleanup commands:
```bash
ws2 pkill -f bot.py
ws3 pkill -f bot.py
internet pkill -f botnet_cnc.py
```

**Defense:** rate-limit abusive clients at the DMZ servers. The defense installs nftables rules on DMZ servers to reject excessive new connections per source IP (HTTP/FTP/DNS/NTP service ports). This preserves normal traffic while throttling floods.

**Execute (VM host):**
```bash
bash protections/protect_botnet.sh
```
Verify: re-run the botnet attack; bots should see more rejected/failed connections and the HTTP service should remain more responsive.

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

**Defense:** block the amplification traffic at the victim. On the HTTP server, we drop the unsolicited UDP replies coming from the reflector port used by this demo (`12345`) so the amplified traffic does not reach the application.

**Execute (VM host):**
```bash
bash protections/protect_reflected_ddos.sh
```
Verify: re-run; UDP amplification replies (port 12345) get dropped on the http server.

---
## ⚠️ Important: Testing sequentially (pairs 1→5)

**Interference warning:** If applying all 5 protections in sequence during one topology session, **some protections will interfere** because multiple scripts flush or overwrite rules on the same hosts:

| Protection applied | Host flushed | What is lost |
|---|---|---|
| `protect_scan.sh` | `r2` | Firewall's rule blocking internet → workstations (`10.1.0.0/24`). After this, internet can reach workstations on ports 80/21 and via ICMP. |
| `protect_ftp_bruteforce.sh` | `ftp` | Firewall's ftp output rules — but they are re-applied by the script itself, so no net loss. |
| `protect_reflected_ddos.sh` | `http` | Firewall's http output rules **and** Pair 4's botnet rate-limiting rule on http. |

Additionally:
- **Pair 2 before Pair 4 (ftp):** `protect_ftp_bruteforce.sh` installs a catch-all DROP rule on ftp port 21. When `protect_botnet.sh` runs afterwards, its rate-limiting rule on port 21 is appended *after* that DROP — it is silently unreachable and never executed. The ftp server is still protected, but only by the brute-force rules.

**Solution: Two testing strategies**

**Strategy A — Isolated testing (recommended for demo):**
1. Test Pair 1 alone: `firewall.sh` → `protect_scan.sh` → demo scan attack → stop topology
2. Restart topology, test Pair 2 alone: `firewall.sh` → `protect_ftp_bruteforce.sh` → demo FTP attack → stop
3. Repeat for pairs 3, 4, 5 separately

**Strategy B — Sequential testing (all pairs in one session):**
1. `firewall.sh`
2. Pair 1: attack + `protect_scan.sh` → test
3. Pair 2: attack + `protect_ftp_bruteforce.sh` → test
4. **Reset:** `bash firewall.sh` (before Pair 3 to clean up ftp rules)
5. Pair 3: attack + `protect_arp_poison.sh` → test (ws2, ws3 not in earlier pairs, so OK)
6. **Reset:** `bash firewall.sh`
7. Pair 4: attack + `protect_botnet.sh` → test
8. **Reset:** `bash firewall.sh`
9. Pair 5: attack + `protect_reflected_ddos.sh` → test

---
## 3) Quick “normal operation” check
From Mininet CLI, a workstation should still be able to access DMZ services:

```bash
ws2 curl http://10.12.0.10/
```
