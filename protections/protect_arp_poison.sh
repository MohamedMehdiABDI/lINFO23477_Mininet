#!/bin/bash
# Protection against ARP Cache Poisoning
# Only accept ARP replies from the legitimate gateway MAC

echo "Applying ARP poisoning protection on workstations..."

GATEWAY_IP="10.1.0.1"
GATEWAY_MAC="82:2b:af:58:7c:80"

for host in ws2 ws3; do
    mnexec -a $(pgrep -f "mininet:$host") nft flush ruleset
    mnexec -a $(pgrep -f "mininet:$host") nft add table arp filter
    mnexec -a $(pgrep -f "mininet:$host") nft add chain arp filter input '{ type filter hook input priority 0 ; policy accept ; }'

    # Drop ARP replies claiming to be the gateway but with wrong MAC
    mnexec -a $(pgrep -f "mininet:$host") nft add rule arp filter input \
        arp operation reply \
        arp saddr ip 10.1.0.1 \
        arp saddr ether != $GATEWAY_MAC \
        drop
done

echo "ARP poisoning protection applied!"
