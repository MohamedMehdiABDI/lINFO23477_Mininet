#!/bin/bash
# Basic enterprise network protection firewall rules

# DMZ servers - cannot initiate connections, can only respond
for host in http dns ntp ftp; do
    echo "Configuring $host..."
    mnexec -a $(pgrep -f "mininet:$host") nft flush ruleset
    mnexec -a $(pgrep -f "mininet:$host") nft add table inet filter
    mnexec -a $(pgrep -f "mininet:$host") nft add chain inet filter output '{ type filter hook output priority 0 ; policy drop ; }'
    mnexec -a $(pgrep -f "mininet:$host") nft add rule inet filter output ct state established,related accept
    mnexec -a $(pgrep -f "mininet:$host") nft add rule inet filter output oif lo accept
    mnexec -a $(pgrep -f "mininet:$host") nft add rule inet filter output icmp type echo-reply accept
done

# r2 - block internet from reaching workstations
echo "Configuring r2..."
mnexec -a $(pgrep -f "mininet:r2") nft flush ruleset
mnexec -a $(pgrep -f "mininet:r2") nft add table inet filter
mnexec -a $(pgrep -f "mininet:r2") nft add chain inet filter forward '{ type filter hook forward priority 0 ; policy accept ; }'
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward iifname "r2-eth0" ip daddr 10.1.0.0/24 ct state new drop
mnexec -a $(pgrep -f "mininet:r2") nft add rule inet filter forward iifname "r2-eth0" ip daddr 10.1.0.0/24 icmp type echo-request drop
# Start services inside correct network namespaces
echo "Starting services..."
mnexec -a $(pgrep -f "mininet:http") bash -c 'source /etc/apache2/envvars && apache2 -D FOREGROUND &'
 
echo "Done!"
