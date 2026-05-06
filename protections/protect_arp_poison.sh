#!/bin/bash
# Protection against ARP Cache Poisoning

echo "Applying ARP poisoning protection on workstations..."
GATEWAY_IP="10.1.0.1"

# Get real gateway MAC dynamically
GATEWAY_MAC=$(mnexec -a $(pgrep -f "mininet:r1") cat /sys/class/net/r1-eth0/address)
echo "[*] Gateway MAC: $GATEWAY_MAC"

for host in ws2 ws3; do
    mnexec -a $(pgrep -f "mininet:$host") nft flush ruleset
    mnexec -a $(pgrep -f "mininet:$host") nft add table arp filter
    mnexec -a $(pgrep -f "mininet:$host") nft add chain arp filter input '{ type filter hook input priority 0 ; policy accept ; }'
    mnexec -a $(pgrep -f "mininet:$host") nft add rule arp filter input \
        arp operation reply \
        arp saddr ip $GATEWAY_IP \
        arp saddr ether != $GATEWAY_MAC \
        drop
done

echo "ARP poisoning protection applied! Gateway MAC: $GATEWAY_MAC"