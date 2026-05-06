---
marp: true
theme: default
paginate: true
style: |
  section {
    font-size: 1.1rem;
  }
  h1 { color: #1c7ed6; }
  h2 { color: #1c7ed6; margin-top: 0; }
  .attack { color: #c0392b; font-weight: bold; }
  .defense { color: #27ae60; font-weight: bold; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
  .box { background: #f8f9fa; border-radius: 8px; padding: 1rem; height: 100%; }
  .box ul { margin: 0.4rem 0 0 0; padding-left: 1.2rem; }
  .box li { margin-bottom: 0.4rem; }
  code { font-size: 0.85rem; }
---

# LINFO2347 — Project 2
## Enterprise Network Security: Attacks & Defenses



## Pair 1 — Network Scan

<div class="cols">
<div class="box">

<span class="attack">Attack</span>

Attacker probes both subnets from the internet to discover live hosts and open services.

- Sends **ICMP echo-requests** to every address in `10.12.0.0/24` and `10.1.0.0/24`
- Sends **TCP SYN** to common ports (21, 22, 80, 5353) — SYN-ACK means open

```
internet python3 attacks/network_scan.py
```

</div>
<div class="box">

<span class="defense">Defense</span>

Reduce scan visibility at the perimeter router `r2`.

- **Rate-limit** ICMP echo-requests from internet to 3/second — excess dropped
- **Block TCP SYN** to any port other than 80 and 21 from the internet side

```
bash protections/protect_scan.sh
```

> Result: attacker sees only HTTP and FTP; SSH, DNS, and internal hosts are hidden.

</div>
</div>

---

## Pair 2 — FTP Brute Force

<div class="cols">
<div class="box">

<span class="attack">Attack</span>

Attacker tries all combinations from a username/password wordlist against `ftp:21`.

- Repeatedly opens TCP connections and sends `USER` / `PASS` commands
- A `230` response means login succeeded
- ~35 attempts with a 0.5 s delay between each

```
internet python3 attacks/ftp_bruteforce.py
```

</div>
<div class="box">

<span class="defense">Defense</span>

Slow the attack to impractical speed using an **nftables meter** on the FTP server.

- Tracks new connections per source IP
- Allows at most **3 new connections per minute** per IP (burst of 3)
- Any further new connection is **dropped**

```
bash protections/protect_ftp_bruteforce.sh
```

> Result: attacker must wait 1 minute between every 3 guesses — wordlist becomes useless.

</div>
</div>

---

## Pair 3 — ARP Cache Poisoning

<div class="cols">
<div class="box">

<span class="attack">Attack</span>

`ws3` poisons `ws2`'s ARP cache to redirect traffic meant for the gateway.

- Sends forged ARP replies to `ws2` claiming:  
  gateway IP `10.1.0.1` → attacker's MAC
- `ws2` updates its cache → all traffic flows through `ws3` (MITM)

```
ws3 python3 attacks/arp_poison.py
```

</div>
<div class="box">

<span class="defense">Defense</span>

**MAC pinning** at the ARP layer on both workstations.

- Installs an ARP `input` filter on `ws2` and `ws3`
- Drops any ARP reply where sender IP = `10.1.0.1` **and** sender MAC ≠ legitimate gateway MAC (`82:2b:af:58:7c:80`)

```
bash protections/protect_arp_poison.sh
```

> Result: forged ARP replies are silently dropped; ws2's cache stays correct.

</div>
</div>

---

## Pair 4 — Botnet HTTP Flood

<div class="cols">
<div class="box">

<span class="attack">Attack</span>

A C&C server coordinates compromised internal hosts to flood the HTTP server.

- C&C (`internet`) waits for bots, then sends `ATTACK` command
- Bots (`ws2`, `ws3`) repeatedly open TCP connections to `http:80` and send HTTP GET requests
- Multiple sources make simple per-IP limiting ineffective

```
internet python3 attacks/botnet_cnc.py
ws2 python3 attacks/bot.py &
ws3 python3 attacks/bot.py &
```

</div>
<div class="box">

<span class="defense">Defense</span>

**Per-source-IP rate limiting** on every DMZ server using nftables meters.

- Installed on `http` (port 80), `ftp` (21), `dns` (5353), `ntp` (123)
- Allows at most **10 new connections per second** per source IP
- Excess connections are **rejected** (immediate RST/ICMP unreachable)

```
bash protections/protect_botnet.sh
```

> Result: each bot is throttled individually; legitimate traffic is preserved.

</div>
</div>

---

## Pair 5 — Reflected UDP DDoS

<div class="cols">
<div class="box">

<span class="attack">Attack</span>

Attacker amplifies traffic toward the victim by abusing an open UDP reflector.

1. Attacker **spoofs** source IP = victim (`http` server)
2. Sends small UDP packets (`~4 B`) to reflector (`ntp:12345`)
3. Reflector replies with **1000 B** to the victim — amplification ×250
4. Victim receives flood without attacker being directly involved

```
ntp python3 attacks/udp_reflector.py &
internet python3 attacks/reflected_ddos.py
```

</div>
<div class="box">

<span class="defense">Defense</span>

**Ingress filtering** on the victim (`http` server) to drop amplified replies before they reach the application.

- Adds an `input` rule: drop all UDP packets with `sport 12345`
- Counter attached to verify drops in real time
- Does not affect legitimate HTTP traffic

```
bash protections/protect_reflected_ddos.sh
```

> Result: amplified UDP packets are discarded at the NIC; HTTP service stays responsive.

</div>
</div>
