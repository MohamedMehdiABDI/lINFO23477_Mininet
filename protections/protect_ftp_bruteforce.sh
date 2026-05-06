#!/bin/bash
# Protection against FTP brute force
# Uses nftables meter to limit new FTP connections to 3 per minute per source IP


echo "Applying FTP brute force protection on ftp server..."

mnexec -a $(pgrep -f "mininet:ftp") nft flush ruleset
mnexec -a $(pgrep -f "mininet:ftp") nft add table inet filter

# Output chain - DMZ server cannot initiate connections
mnexec -a $(pgrep -f "mininet:ftp") nft add chain inet filter output '{ type filter hook output priority 0 ; policy drop ; }'
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter output ct state established,related accept
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter output oif lo accept
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter output icmp type echo-reply accept

# Input chain - rate limit new FTP connections
mnexec -a $(pgrep -f "mininet:ftp") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter input iif lo accept
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter input ct state established,related accept

# Allow max 3 new connections per minute per source IP
# After 3 attempts the attacker must wait 1 minute before trying again
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter input tcp dport 21 ct state new meter ftp_limit '{ ip saddr limit rate 3/minute burst 3 packets }' accept
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter input tcp dport 21 ct state new drop

echo "FTP brute force protection applied!"
