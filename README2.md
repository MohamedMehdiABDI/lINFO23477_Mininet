# LINFO2347 — Project 2: Enterprise Network Security

Small enterprise network simulation in Mininet demonstrating a basic firewall policy and 5 attack/defense pairs.

---

## Network Topology

```
[Internet 10.2.0.2]
        |
       r2  (internet gateway)
        |
   DMZ 10.12.0.0/24
   http(10.12.0.10)  dns(10.12.0.20)  ntp(10.12.0.30)  ftp(10.12.0.40)
        |
       r1  (internal router)
        |
   Workstations 10.1.0.0/24
   ws2(10.1.0.2)  ws3(10.1.0.3)
```

---

## Basic Enterprise Network Protection (`firewall.sh`)

The baseline firewall is implemented with **nftables** and enforces two policies.

### DMZ servers — no outbound initiation

Applied to `http`, `dns`, `ntp`, `ftp`:

- Output chain policy: **DROP**
- Exceptions allowed: replies to established/related connections, ICMP echo-reply, loopback

This prevents a compromised DMZ server from initiating connections to the internet or internal workstations; it can only respond to traffic directed at it.

### Router r2 — internet cannot reach workstations

Applied to the `forward` chain on `r2`:

- Drops new TCP connections from `r2-eth0` (internet side) destined to `10.1.0.0/24`
- Drops ICMP echo-requests from `r2-eth0` destined to `10.1.0.0/24`

Workstations can freely initiate connections outward; only inbound-initiated traffic from the internet is blocked.

> After applying `firewall.sh`, `pingall` in Mininet will not fully succeed — this is expected.

---

## Execution Instructions

### 1. Start the topology

From this directory, on the VM host:

```bash
sudo -E python3 topo.py YOURNOMA   # YOURNOMA = your student NOMA number
```

This opens the Mininet CLI. Keep it open throughout.

### 2. Apply the baseline firewall

In a **separate terminal** on the VM host:

```bash
bash firewall.sh
```

### 3. Attack / Defense pairs

Run **attacks** from the Mininet CLI. Run **defenses** from the VM host terminal.

---

#### Pair 1 — Network scan

**Attack:** probes both subnets with ICMP and TCP SYN to discover live hosts and open ports.

```bash
# Mininet CLI
internet python3 attacks/network_scan.py
```

**Defense:** rate-limits ICMP from the internet and blocks TCP SYN to non-public ports on `r2`.

```bash
# VM host
bash protections/protect_scan.sh
```

---

#### Pair 2 — FTP brute force

**Attack:** tries common username/password combinations against the FTP server (`10.12.0.40:21`).

```bash
# Mininet CLI
internet python3 attacks/ftp_bruteforce.py
```

**Defense:** limits new FTP connections to 3 per minute per source IP using an nftables meter on the `ftp` server.

```bash
# VM host
bash protections/protect_ftp_bruteforce.sh
```

---

#### Pair 3 — ARP cache poisoning

**Attack:** `ws3` sends forged ARP replies to `ws2` claiming the attacker's MAC owns the gateway IP, enabling MITM on the LAN.

```bash
# Mininet CLI
ws3 python3 attacks/arp_poison.py
```

**Defense:** installs an ARP input filter on `ws2` and `ws3` that drops any ARP reply claiming to be the gateway (`10.1.0.1`) with an unexpected MAC address.

```bash
# VM host
bash protections/protect_arp_poison.sh
```

---

#### Pair 4 — Botnet HTTP flood

**Attack:** a C&C server coordinates two bots (ws2, ws3) to flood the HTTP server with connections.

```bash
# Mininet CLI — start C&C first (waits 10 s for bots)
internet python3 attacks/botnet_cnc.py
# then quickly in separate CLI lines:
ws2 python3 attacks/bot.py &
ws3 python3 attacks/bot.py &
```

**Defense:** rate-limits new connections per source IP (10/s) on all DMZ servers using nftables meters.

```bash
# VM host
bash protections/protect_botnet.sh
```

---

#### Pair 5 — Reflected UDP DDoS

**Attack:** the attacker spoofs the victim's IP and sends small UDP requests to a reflector; the reflector sends large replies to the victim, amplifying the traffic.

```bash
# Mininet CLI — start reflector first
ntp python3 attacks/udp_reflector.py &
# then launch the attack
internet python3 attacks/reflected_ddos.py
```

**Defense:** drops unsolicited UDP packets arriving on the amplification port (sport 12345) on the `http` server.

```bash
# VM host
bash protections/protect_reflected_ddos.sh
```

---

### Testing note

Re-run `bash firewall.sh` to reset nftables rules before testing each pair. Some protection scripts flush rules on shared hosts, which can silently interfere when pairs are applied in sequence (see README.md for details).
