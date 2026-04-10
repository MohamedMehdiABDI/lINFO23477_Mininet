#!/bin/bash
# Protection against network scan on r2

echo "Applying scan protection on r2..."

mnexec -a $(pgrep -f "mininet:r2") nft flush ruleset
mnexec -a $(pgrep -f "mininet:r2") nft add table inet filter
mnexec -a $(pgrep -f "mininet:r2") nft add chain inet filter forward '{ type filter hook forward priority 0 ; policy accept ; }'

# Block ICMP echo requests coming from internet side
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward \
    iifname "r2-eth0" \
    icmp type echo-request \
    limit rate over 3/second \
    drop

# Block TCP SYN packets to ports that should not be publicly accessible
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward \
    iifname "r2-eth0" \
    ip protocol tcp \
    tcp flags syn \
    tcp dport != { 80, 21 } \
    drop

echo "Scan protection applied!"
