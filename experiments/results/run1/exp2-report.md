# Evaluationsbericht: Experiment 2 – Fehlerhaftes Deployment & Git Revert

> **Datum:** 01.10.2026, 10:05 Uhr (UTC 08:05)  
> **Initialer Commit:** `9a3468f`  
> **Fehlerhafter Release-Commit:** `05e2318` (Readiness-Probe auf ungültigen Endpunkt)  
> **Revert-Commit:** `2d34aca`  
> **Cluster:** k3s auf AWS EC2 (`t3.small`, eu-central-1)  

---

## 1. Versuchsaufbau & Hypothese

- **Hypothese:** Ein neues Application-Release mit defekter Readiness-Probe darf den Produktivbetrieb bestehender Instanzen nicht beeinträchtigen. Die Rolling-Update-Strategie (`maxUnavailable: 0`) hält alte Pods aktiv, solange die neuen Instanzen nicht `Ready` melden. Ein anschließender `git revert` stellt den alten Zustand deterministisch wieder her.

---

## 2. Gemessene Kennzahlen

| Phase | Dauer | Anfragen | Erfolgreich (200 OK) | Fehlerrate | Systemzustand |
|---|---|---|---|---|---|
| **Fehlerhafter Rollout** | 20 s | 200 | 200 | **0,00 %** | Neuer Pod `0/1 NotReady`, Rollout pausiert, Bestands-Pods bedienen Traffic |
| **Git Revert & Sync** | 37,19 s | — | — | — | Argo CD synchronisiert Revert, terminiert defekten Pod, stellt `Healthy` her |

---

## 3. Fazit für die Projektarbeit

Das Zusammenspiel aus Kubernetes-Readiness-Probes und GitOps schützt den Produktivbetrieb vollständig vor fehlerhaften Releases:
1. Keine einzige Endbenutzer-Anfrage schlug fehl (**0,0 % Fehlerrate**).
2. Der Rollout wurde automatisch gestoppt.
3. Die Wiederherstellung über `git revert` erfolgte innerhalb von **37 Sekunden**.
