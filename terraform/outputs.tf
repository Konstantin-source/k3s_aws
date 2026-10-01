output "public_ip" {
  description = "Öffentliche IP-Adresse (Elastic IP) des k3s Servers"
  value       = aws_eip.k3s_eip.public_ip
}

output "ssh_connection_command" {
  description = "Befehl zur SSH-Verbindung mit der EC2-Instanz"
  value       = "ssh ubuntu@${aws_eip.k3s_eip.public_ip}"
}

output "resilience_lab_url" {
  description = "Öffentliche URL des Resilience Lab (HTTP Ingress)"
  value       = "http://${aws_eip.k3s_eip.public_ip}"
}

output "argocd_ui_url" {
  description = "Öffentliche URL der Argo CD Web-Oberfläche"
  value       = "http://${aws_eip.k3s_eip.public_ip}:30080"
}

output "kubeconfig_fetch_command" {
  description = "Befehl zum Abrufen der Kubeconfig-Datei auf den lokalen Rechner"
  value       = "scp ubuntu@${aws_eip.k3s_eip.public_ip}:/home/ubuntu/.kube/config ./kubeconfig-aws.yaml"
}

output "argocd_initial_password_command" {
  description = "Befehl zum Auslesen des initialen Argo CD Admin-Passworts"
  value       = "ssh ubuntu@${aws_eip.k3s_eip.public_ip} 'sudo kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d && echo'"
}
