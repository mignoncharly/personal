#!/usr/bin/env bash
#
# fix-server-stability.sh
# Addresses the VS Code / SSH disconnects caused by server instability.
# Root cause (15 Jun 2026): 3.8 GB RAM with ZERO swap + a crash-looping
# service (amtklarpro) => memory stalls (kernel hung_task) and reboots that
# drop the SSH/VS Code Remote connection.
#
# Safe & idempotent. Review, then run:   sudo bash scripts/fix-server-stability.sh
set -euo pipefail

echo "==> 1/4  Adding a 4 GB swap file (none exists today)"
if swapon --show | grep -q .; then
  echo "    swap already active — skipping"
else
  fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  if ! grep -q '^/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
  echo "    swap on:"; swapon --show
fi

echo "==> 2/4  Tuning vm.swappiness=10 (use swap only under real pressure)"
sysctl -w vm.swappiness=10
install -d /etc/sysctl.d
echo 'vm.swappiness=10' > /etc/sysctl.d/99-swappiness.conf

echo "==> 3/4  Stopping the crash-looping amtklarpro service"
echo "    (its working dir /var/www/amtklarpro does not exist -> fails forever)"
if systemctl list-unit-files | grep -q '^amtklarpro-simple.service'; then
  systemctl stop amtklarpro-simple.service || true
  systemctl disable amtklarpro-simple.service || true
  echo "    stopped & disabled. Re-enable later with: sudo systemctl enable --now amtklarpro-simple.service"
else
  echo "    service not present — skipping"
fi

echo "==> 4/4  Enabling SSH server keepalive (prevents silent idle drops)"
install -d /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/99-keepalive.conf <<'EOF'
ClientAliveInterval 60
ClientAliveCountMax 3
TCPKeepAlive yes
EOF
if sshd -t; then
  systemctl reload ssh || systemctl reload sshd || true
  echo "    sshd config valid and reloaded"
else
  echo "    !! sshd config test FAILED — not reloading; review /etc/ssh/sshd_config.d/99-keepalive.conf"
fi

echo
echo "==> DONE. Current memory:"
free -h
