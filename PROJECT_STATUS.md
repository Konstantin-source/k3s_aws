# Projektübersicht & Status: GitOps-basiertes Kubernetes-Labor auf AWS mit k3s

> **VERBINDLICHE ANWEISUNG:**
> 1. Die gesamte Projektarbeit wird ausnahmslos in **LaTeX** verfasst.
> 2. Der sprachliche Stil und die Textgestaltung richten sich zwingend nach `styles.md` (vorläufig orientiert an `ThreadstormDoku (1).pdf` und den RH-Köln-Leitfaden-Vorgaben).
> 3. Keine kostenpflichtigen AWS-Ressourcen werden ohne vorherige Freigabe der Architektur und Kostenschätzung erzeugt.

---

## 1. Projektdaten

- **Thema:** Aufbau und Evaluation einer GitOps-basierten Kubernetes-Umgebung auf AWS mit k3s durch kontrollierte Fehlerexperimente
- **Hochschule:** Rheinische Hochschule Köln (Fachbereich Ingenieurwesen / Informatik B.Sc.)
- **Erstprüfer:** Prof. Dr. Johannes Mauer (vorläufig angenommen gem. Vorlage Threadstorm)
- **Autor:** Konstantin Muschallik
- **Status:** Vorbereitung & lokale Entwicklung

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
- **Argo CD:** Verwaltet alle Anwendungsressourcen per GitOps (Deployments, Services, Ingress, ConfigMaps).
- **Helm:** Paketiert die Anwendungskonfiguration (`resilience-lab`) mit sauberen Werten für lokal (`values-local.yaml`) und AWS (`values-aws.yaml`).
- **Anwendung:** Leichtgewichtige REST-API (Python/FastAPI oder Go) mit HTML-Statusoberfläche und geschütztem `/lab`-Endpunkt für Störungsinduktion.
- **Lastmessung:** k6 / Python-Messskripte für Latenzen (p50/p95), HTTP-Fehlerraten und Erholzeiten.

---

## 4. Fortschritt & Phasen

- [x] Dateisichtung beider Repositories (`k3s_aws` & `leitfaden-main_10.2025`)
- [x] Analyse der Threadstorm-Referenzarbeit & des RH-Leitfadens
- [x] Architektur-Umstellung auf k3s + EC2 (Kostenersparnis ~22 $/Monat statt ~187 $/Monat für EKS)
- [x] Projektübersicht (`PROJECT_STATUS.md`) und `.gitignore` angelegt
- [ ] Vorläufige `styles.md` definiert und zur Prüfung bereitgestellt
- [ ] LaTeX-Vorlage im Ordner `thesis/` eingerichtet und kompiliert
- [ ] Demo-Webanwendung (`app/`) implementiert
- [ ] Helm-Chart (`helm/resilience-lab`) erstellt
- [ ] Lokale Validierung im Container / lokalen Kubernetes
- [ ] Terraform-Code (`terraform/`) verfasst
- [ ] Kostenfreigabe vor AWS-Bereitstellung eingeholt
- [ ] Experimente durchgeführt & Messdaten erfasst
- [ ] LaTeX-Ausarbeitung verfasst und geprüft

---

## 5. Offene Fragen & Klärungsbedarf
(Siehe aktuelle Fragenabfrage im Dialog)
