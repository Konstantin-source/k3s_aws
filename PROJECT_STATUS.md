# Projektübersicht & Status: GitOps-basiertes Kubernetes-Labor auf AWS mit k3s

> **VERBINDLICHE ANWEISUNG:**
> 1. Die gesamte Projektarbeit wird ausnahmslos in **LaTeX** verfasst.
> 2. Der sprachliche Stil und die Textgestaltung richten sich zwingend nach `styles.md` (vorläufig orientiert an `ThreadstormDoku (1).pdf` und den RH-Köln-Leitfaden-Vorgaben).
> 3. Im Quellcode gelten ausschließlich sporadische, umgangssprachliche Kommentare (keine großen Blöcke).
> 4. Keine kostenpflichtigen AWS-Ressourcen werden ohne vorherige Freigabe der Architektur und Kostenschätzung erzeugt.

---

## 1. Projektdaten

- **Thema:** Aufbau und Evaluation einer GitOps-basierten Kubernetes-Umgebung auf AWS mit k3s durch kontrollierte Fehlerexperimente
- **Hochschule:** Rheinische Hochschule Köln (Fachbereich Ingenieurwesen / Informatik B.Sc.)
- **Erstprüfer:** Prof. Dr. Johannes Mauer
- **Autor:** Konstantin Muschallik
- **Status:** Vorbereitung & lokale Entwicklung
- **Umfang:** Ca. 25–35 Seiten Textteil
- **Zeitrahmen:** 2–3 Monate (Semesterende)

---

## 2. Kernziel & Fragestellung

### Leitfrage
> *Inwieweit verbessern automatisierte Bereitstellung mittels Infrastructure as Code (Terraform) und GitOps-gesteuerte Synchronisation (Argo CD) die Ausfallsicherheit und Wiederherstellungsfähigkeit einer Webanwendung auf einer kosteneffizienten Kubernetes-Umgebung (k3s auf AWS EC2) gegenüber manuell verwalteten Deployments?*

### Überprüfbare Erwartungen & Kernexperimente
1. **Experiment 1 (Prozessabsturz):** Kubernetes stellt nach einem erzwungenen Absturz (`/lab/crash`) den Dienst via Pod-Neustart wieder her; bei $\ge 2$ Replikaten bleibt der Dienst ohne dauerhaften Ausfall für Anfragen erreichbar.
2. **Experiment 2 (Fehlerhaftes Deployment):** Ein Rolling Update mit fehlschlagender Readiness-Probe (`/health/ready`) belässt den bestehenden stabilen Pod im Datenverkehr; ein Git-Revert stellt den Sollzustand reproduzierbar wieder her.
3. **Experiment 3 (Konfigurationsabweichung):** Eine direkte Cluster-Manipulation (z. B. Skalierung oder Env-Änderung) wird durch Argo CD Self-Heal automatisch auf den Git-Sollzustand zurückgesetzt.

---

## 3. Architektur & Werkzeugaufteilung

- **Terraform:** Verwaltet ausschließlich die AWS-Basisinfrastruktur (VPC, Subnetze, Security Groups, EC2-Instanz, Elastic IP).
- **cloud-init (user-data):** Einmaliger automatischer Bootstrap von k3s (leichtgewichtige Kubernetes-Distribution) und Argo CD auf der EC2-Instanz.
- **Argo CD:** Verwaltet alle Anwendungsressourcen per GitOps (Deployments, Services, Ingress).
- **Kustomize:** Deklarative Manifeststrukturierung ohne Templating-Overhead (`kustomize/base`, `kustomize/overlays/local`, `kustomize/overlays/aws`).
- **Anwendung:** Leichtgewichtige REST-API (Python/FastAPI) mit HTML-Statusoberfläche und geschütztem `/lab`-Endpunkt für Störungsinduktion.
- **Lastmessung:** Python- & k6-Messskripte für Latenzen (p50/p95), HTTP-Fehlerraten und Erholzeiten.

---

## 4. Fortschritt & Phasen

- [x] Dateisichtung beider Repositories (`k3s_aws` & `leitfaden-main_10.2025`)
- [x] Analyse der Threadstorm-Referenzarbeit & des RH-Leitfadens
- [x] Architektur-Umstellung auf k3s + EC2 (Kostenersparnis ~22 $/Monat statt ~187 $/Monat für EKS)
- [x] Wechsel von Helm auf Kustomize (nativ in kubectl und Argo CD integriert)
- [x] Projektübersicht (`PROJECT_STATUS.md`) und `.gitignore` angelegt
- [x] Vorläufige `styles.md` definiert
- [x] LaTeX-Vorlage im Ordner `thesis/` eingerichtet (9 Kapitel strukturiert)
- [x] Demo-Webanwendung (`app/`) mit Dashboard und Störungsendpunkten implementiert
- [x] Kustomize-Overlays (`kustomize/base`, `local`, `aws`) erstellt und validiert
- [x] Argo CD Application-Manifest auf Kustomize angepasst
- [x] Terraform-Code (`terraform/`) verfasst
- [x] GitHub Actions CI-Pipeline (`.github/workflows/ci.yml`) erstellt
- [x] AWS-Konto & Zugriffs-Check (lokales AWS CLI)
- [x] Kostenfreigabe vor AWS-Bereitstellung eingeholt
- [x] Infrastruktur via Terraform auf AWS bereitgestellt (k3s + Argo CD)
- [x] Experiment 3 (Configuration Drift & Self-Heal) erfolgreich durchgeführt & dokumentiert (Erkennung: 2,58s, Wiederherstellung: 11,28s)
- [ ] Experiment 1 (Prozessabsturz) mit Hintergrundlast messen
- [ ] Experiment 2 (Fehlerhaftes Deployment) durchführen
- [x] LaTeX-Ausarbeitung mit konkreten Messergebnissen aktualisiert
