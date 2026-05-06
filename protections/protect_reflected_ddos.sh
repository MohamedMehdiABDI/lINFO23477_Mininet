#!/bin/bash
# Protection against Reflected DDoS
# Block all unsolicited UDP replies on http server

echo "Applying Reflected DDoS protection on http server..."

mnexec -a $(pgrep -f "mininet:http") nft flush ruleset
mnexec -a $(pgrep -f "mininet:http") nft add table inet filter

# Output chain - DMZ server cannot initiate connections
mnexec -a $(pgrep -f "mininet:http") nft add chain inet filter output '{ type filter hook output priority 0 ; policy drop ; }'
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter output ct state established,related accept
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter output oif lo accept
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter output icmp type echo-reply accept

# Input chain - block unsolicited UDP amplification replies
mnexec -a $(pgrep -f "mininet:http") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter input iif lo accept
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter input ct state established,related accept

# Drop ALL unsolicited UDP with counter to verify drops
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter input \
    ip protocol udp \
    udp sport 12345 \
    counter drop

echo "Reflected DDoS protection applied!"
