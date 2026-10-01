# Installations- und Ausführungsanleitung (Setup Guide)

## 1. Lokale Entwicklung & Test der Anwendung

### Direkt mit Python
```bash
cd app
pip install -r requirements.txt
python main.py
# Öffne http://localhost:8000 im Browser
```

### Mit Docker
```bash
docker build -t resilience-lab:1.0.0 app/
docker run -p 8000:8000 --name lab resilience-lab:1.0.0
# Öffne http://localhost:8000 im Browser
```

---

## 2. Bereitstellung auf AWS mit Terraform

> **Wichtig:** Voraussetzung ist ein konfiguriertes AWS CLI (`aws configure`) oder gesetzte Umgebungsvariablen (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).

```bash
cd terraform

# 1. Initialisierung
terraform init

# 2. Trockenlauf (Plan anzeigen)
terraform plan

# 3. Bereitstellung (erst nach deiner Freigabe)
terraform apply -auto-approve

# 4. Outputs anzeigen (IP, SSH, URLs)
terraform output
```

### Nach dem Deployment (ca. 2-3 Minuten für Cloud-Init):
- **Web-UI Resilience Lab:** `http://<PUBLIC_IP>`
- **Argo CD UI:** `http://<PUBLIC_IP>:30080` (User: `admin`)
- **Initiales Argo CD Passwort abrufen:**
  ```bash
  ssh ubuntu@<PUBLIC_IP> 'sudo kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo'
  ```
- **Kubeconfig für lokalen `kubectl`-Zugriff herunterladen:**
  ```bash
  scp ubuntu@<PUBLIC_IP>:/home/ubuntu/.kube/config ./kubeconfig-aws.yaml
  export KUBECONFIG=$(pwd)/kubeconfig-aws.yaml
  kubectl get nodes
  ```

---

## 3. Argo CD Application registrieren

```bash
kubectl apply -f argocd/application.yaml
```
Argo CD synchronisiert nun das Helm-Chart und stellt das Resilience Lab automatisch bereit.
