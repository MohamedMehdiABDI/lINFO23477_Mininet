#!/bin/bash
# Protection against botnet HTTP flood
# Adds per-IP rate limiting on each DMZ server's service port
# Compatible with basic_protection.sh (adds input chain to existing table)

# HTTP server - port 80
echo "Protecting HTTP server..."
mnexec -a $(pgrep -f "mininet:http") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:http") nft add rule inet filter input tcp dport 80 ct state new meter flood size 65535 { ip saddr limit rate over 10/second } reject

# FTP server - port 21
echo "Protecting FTP server..."
mnexec -a $(pgrep -f "mininet:ftp") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:ftp") nft add rule inet filter input tcp dport 21 ct state new meter flood size 65535 { ip saddr limit rate over 10/second } reject

# DNS server - port 5353
echo "Protecting DNS server..."
mnexec -a $(pgrep -f "mininet:dns") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:dns") nft add rule inet filter input udp dport 5353 ct state new meter flood size 65535 { ip saddr limit rate over 10/second } reject

# NTP server - port 123
echo "Protecting NTP server..."
mnexec -a $(pgrep -f "mininet:ntp") nft add chain inet filter input '{ type filter hook input priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:ntp") nft add rule inet filter input udp dport 123 ct state new meter flood size 65535 { ip saddr limit rate over 10/second } reject

echo "Botnet protection applied on all DMZ servers!"
