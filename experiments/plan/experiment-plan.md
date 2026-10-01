# Versuchsplan: Kontrollierte Fehlerexperimente im Resilience Lab

> **Ziel:** Empirische Untersuchung der Selbstheilungs- und Ausfallsicherheitsmechanismen einer GitOps-basierten Kubernetes-Umgebung (k3s auf AWS EC2) unter kontrollierten Störbedingungen.

---

## 1. Messkonfiguration & Lastprofil

- **Lastgenerator:** [k6](https://k6.io) (JavaScript-basiertes Performancetest-Werkzeug)
- **Lastprofil:**
  - 10 bis 20 Virtuelle Benutzer (VUs)
  - Zielendpunkt: `GET /` bzw. `GET /api/info`
  - Dauer pro Testlauf: 120 Sekunden
  - Hintergrundlast läuft kontinuierlich und unabhängig von den Störauslösungen
- **Erfasste Kennzahlen:**
  - HTTP-Erfolgsrate (2xx Anteil in %)
  - Anzahl fehlgeschlagener Anfragen (5xx / Verbindungsabbrüche)
  - Antwortzeit-Verteilung: Median ($p_{50}$), 95. Perzentil ($p_{95}$)
  - Wiederherstellungszeit ($\text{MTTR}$): Zeitspanne vom ersten Fehler bis zur dauerhaften Stabilisierung

---

## 2. Verbindliche Kernexperimente

### Experiment 1: Abrupter Prozessabsturz
- **Hypothese:** Ein Containerabsturz in der Basiskonfiguration (1 Pod) führt zu spürbaren Verbindungsabbrüchen. In der verbesserten Konfiguration ($\ge 2$ Pods) leitet der Service den Verkehr unterbrechungsfrei an den gesunden Pod weiter.
- **Ablauf:**
  1. Start der Hintergrundlast via `k6 run k6-load-test.js`
  2. Nach 30 Sekunden: Forcierter Absturz via `POST /lab/crash` auf einer Pod-Instanz
  3. Beobachtung des Kubelet-Verhaltens (`RestartCount`, Pod-Neustart via RestartPolicy)
  4. Messung der Ausfallzeit und Wiederherstellungsdauer

### Experiment 2: Fehlerhaftes Deployment (Readiness Failure)
- **Hypothese:** Ein Update auf ein fehlerhaftes Image (Readiness Probe schlägt fehl) wird durch die Rolling-Update-Strategie gestoppt. Die bestehende gesunde Instanz bleibt durchgehend im Traffic; ein `git revert` stellt den alten Zustand wieder her.
- **Ablauf:**
  1. Hintergrundlast aktiv
  2. Ausrollen eines Image-Tags mit fehlerhafter Readiness (`v-broken`)
  3. Überprüfung des Rolling Update Status (`kubectl rollout status`)
  4. Bestätigung: Der neue Pod wird wegen schlagender Readiness-Probe nicht in den Service aufgenommen
  5. Git-Revert im Repository → Argo CD synchronisiert den stabilen Zustand zurück

### Experiment 3: Konfigurationsabweichung (Configuration Drift & Self-Heal)
- **Hypothese:** Eine direkte, unautorisierte Cluster-Modifikation (`kubectl scale --replicas=0`) wird von Argo CD automatisch als Drift erkannt und via Self-Heal binnen kürzester Frist überschrieben.
- **Ablauf:**
  1. Manuelle Reduzierung der Replikate auf 0 direkt im Cluster
  2. Stoppuhr startet: Zeit bis Argo CD den Drift (`OutOfSync`) detektiert
  3. Argo CD Self-Heal greift und skaliert das Deployment wieder auf den Git-Sollwert (2 Replicas)
  4. Protokollierung der Sync-Dauer

---

## 3. Protokollvorlage für Messergebnisse

| Experiment | Konfiguration | Fehlerrate (%) | Latenz $p_{50}$ (ms) | Latenz $p_{95}$ (ms) | Wiederherstellungszeit MTTR (s) |
|---|---|---|---|---|---|
| Exp 1: Crash | 1 Replica (Basis) | *[geplant]* | *[geplant]* | *[geplant]* | *[geplant]* |
| Exp 1: Crash | 2 Replicas (Verbessert) | *[geplant]* | *[geplant]* | *[geplant]* | *[geplant]* |
| Exp 2: Bad Deploy | Rolling Update | *[geplant]* | *[geplant]* | *[geplant]* | *[geplant]* |
| Exp 3: Config Drift | Self-Heal aktiv | *[geplant]* | *[geplant]* | *[geplant]* | *[geplant]* |
