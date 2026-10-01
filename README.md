# GitOps-basiertes Kubernetes-Labor auf AWS mit k3s

> **Praxistransferprojekt im Studiengang Informatik (B.Sc.)**  
> **Rheinische Hochschule Köln (Fachbereich Ingenieurwesen)**  
> **Autor:** Konstantin Muschallik  
> **Erstprüfer:** Prof. Dr. Johannes Mauer  

---

## 📌 Übersicht & Zielsetzung

Dieses Repository enthält den vollständigen Quellcode, die Infrastruktur-Definitionen und die wissenschaftliche Ausarbeitung für das Praxistransferprojekt:

> *„Aufbau und Evaluation einer GitOps-basierten Kubernetes-Umgebung auf AWS mit k3s durch kontrollierte Fehlerexperimente“*

Ziel ist die Untersuchung automatisierter Bereitstellungsmethoden (Infrastructure as Code via **Terraform**) und kontinuierlicher Konfigurationsabgleiche (GitOps via **Argo CD** mit **Kustomize**) zur Steigerung der Ausfallsicherheit von Webanwendungen auf einer ressourcenschonenden, kostengünstigen Kubernetes-Plattform (**k3s auf AWS EC2**).

---

## 📂 Repository-Struktur

```
k3s_aws/
├── PROJECT_STATUS.md       # Laufende Projektübersicht & Status-Tracking
├── styles.md               # Verbindliche sprachliche Stilvorgaben für die Arbeit
├── app/                    # Python/FastAPI Demo-Webanwendung (Resilience Lab)
│   ├── main.py             # REST-API, Statusseite & Störungs-Endpunkte (/lab)
│   ├── templates/          # Modernes HTML/JS Dashboard mit Live-Polling
│   ├── Dockerfile          # Sicheres Container-Image (Non-Root User)
│   └── requirements.txt    # Abhängigkeiten (FastAPI, Uvicorn, Jinja2)
├── kustomize/              # Deklarative Kubernetes-Manifeste ohne Templating
│   ├── base/               # Basis-Ressourcen (Deployment & Service)
│   └── overlays/           
│       ├── local/          # Patch für lokale Umgebung (NodePort, 1 Replikat)
│       └── aws/            # Patch für AWS (2 Replikate, Traefik Ingress)
├── terraform/              # AWS-Infrastruktur als Code
│   ├── versions.tf         # Provider & Mindestversionen
│   ├── variables.tf        # Parametrisierung (Region, Instanztyp)
│   ├── vpc.tf              # VPC, Subnetze, Routing & Internet Gateway
│   ├── security-groups.tf  # Firewall-Regeln (SSH, HTTP, HTTPS, K8s API)
│   ├── ec2.tf              # Ubuntu 24.04 VM mit t3.small
│   ├── eip.tf              # Feste Elastic IP
│   ├── outputs.tf          # Verbindungsbefehle & URLs
│   └── scripts/cloud-init  # Vollautomatischer k3s- & Argo-CD-Bootstrap
├── argocd/                 # GitOps Application-Manifeste
│   └── application.yaml    # Argo CD App mit Automated Sync & Self-Heal
├── experiments/            # Versuchsplanung, Lasttests & Auswertung
│   ├── plan/               # Detaillierter Versuchsplan für die 3 Kernexperimente
│   └── scripts/            # Python- & k6-Lastgeneratoren mit Latenzmetriken
├── docs/                   # Betriebs- & Kostendokumentation
│   ├── setup.md            # Schritt-für-Schritt Inbetriebnahmeanleitung
│   ├── cost-estimate.md    # Transparente AWS-Kostenschätzung (~22 USD/Monat)
│   └── teardown.md         # Vollständiger Abbau & Kostenverifikation
├── thesis/                 # Vollständige LaTeX-Projektarbeit (RH-Köln-Vorlage)
│   ├── dokumentation.tex   # Hauptdokument (report-Klasse, 11pt, Chicago-Stil)
│   ├── quellen.bib         # Literatur- und Quellenverzeichnis
│   ├── abschnitte/         # 9 modulare Kapitel (Einleitung bis Fazit)
│   ├── zusatz/             # Titelblätter, Abkürzungen, Eigenständigkeitserklärung
│   └── bilder/             # Grafiken und Schaubilder
└── .github/workflows/      # CI/CD-Pipelines
    └── ci.yml              # Testen, Docker-Build & Push nach GitHub Packages (GHCR)
```

---

## ⚡ Schnellstart: Lokale Ausführung der Anwendung

```bash
cd app
pip install -r requirements.txt
python main.py
```
Öffne anschließend [http://localhost:8000](http://localhost:8000) im Browser.

---

## 🧪 Die 3 verbindlichen Kernexperimente

1. **Prozessabsturz (`/lab/crash`):** Überprüfung der automatischen Kubelet-Selbstreparatur und Traffic-Absicherung bei Multi-Replica-Betrieb.
2. **Fehlerhaftes Deployment (`/health/ready`):** Validierung, dass schlagende Readiness-Probes den Rollout stoppen und Bestandsinstanzen den Dienstbetrieb sichern.
3. **Konfigurationsdrift:** Direkte Cluster-Manipulation (z. B. Skalierung auf 0) wird von Argo CD automatisch erkannt und durch das aktivierte *Self-Heal* korrigiert.

---

## 📄 Schriftliche Projektarbeit (LaTeX)

Die schriftliche Ausarbeitung befindet sich im Verzeichnis `thesis/` und basiert auf der offiziellen Vorlage der Rheinischen Hochschule Köln.
- **Kompilierung:** LuaLaTeX (`latexmk -lualatex -synctex=1 dokumentation.tex`)
- **Stil:** Verbindlich ausgerichtet an `styles.md`
