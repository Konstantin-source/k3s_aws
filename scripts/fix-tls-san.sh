#!/bin/bash
set -e
sudo mkdir -p /etc/rancher/k3s
sudo bash -c 'cat <<EOF > /etc/rancher/k3s/config.yaml
tls-san:
  - 63.176.27.134
EOF'
sudo systemctl restart k3s
sleep 5
sudo systemctl status k3s --no-pager
