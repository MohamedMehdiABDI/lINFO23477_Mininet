#!/bin/bash
# Protection against network scan on r2
echo "Applying scan protection on r2..."

mnexec -a $(pgrep -f "mininet:r2") nft add table inet filter 2>/dev/null
mnexec -a $(pgrep -f "mininet:r2") nft add chain inet filter forward '{ type filter hook forward priority 0 ; policy accept ; }' 2>/dev/null

# Allow established/related FIRST so legitimate responses pass
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward ct state established,related accept

# Block ICMP echo-requests from internet (rate limited)
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward \
  iifname "r2-eth0" \
  icmp type echo-request \
  limit rate over 3/second \
  drop

# Block NEW TCP SYN packets to non-public ports (only new connections from internet)
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward \
  iifname "r2-eth0" \
  tcp flags syn \
  ct state new \
  tcp dport != { 80, 21 } \
  drop

echo "Scan protection applied!"