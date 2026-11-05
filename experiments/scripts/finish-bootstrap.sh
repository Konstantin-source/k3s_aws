#!/bin/bash
# schliesst das cloud-init bootstrap manuell ab
set -e
IP=$1
kubectl apply --server-side --force-conflicts -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
cat > /tmp/np.json <<'EOF'
{"spec":{"type":"NodePort","ports":[{"port":80,"targetPort":8080,"nodePort":30080,"name":"http"}]}}
EOF
kubectl patch svc argocd-server -n argocd --patch-file /tmp/np.json
mkdir -p /etc/rancher/k3s
printf 'tls-san:\n  - %s\n' "$IP" > /etc/rancher/k3s/config.yaml
systemctl restart k3s
sleep 8
mkdir -p /home/ubuntu/.kube
cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
sed -i "s/127.0.0.1/$IP/g" /home/ubuntu/.kube/config
chown -R ubuntu:ubuntu /home/ubuntu/.kube
echo BOOTSTRAP_DONE
