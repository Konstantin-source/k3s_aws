# Evaluationsbericht: Experiment 3 – Konfigurationsabweichung & Self-Heal

> **Datum:** 01.10.2026, 09:55 Uhr (UTC 07:55)  
> **Git-Commit:** `07a858dac10fe5e76bec13440a743e7a9331bd21`  
> **Image-Version:** `ghcr.io/konstantin-source/resilience-lab:1.0.0`  
> **Cluster:** k3s v1.36.4 auf AWS EC2 (`t3.small`, eu-central-1)  
> **GitOps Controller:** Argo CD v2.14 / v3.0 mit aktiviertem `SelfHeal`  

---

## 1. Versuchsaufbau & Hypothese

- **Hypothese:** Eine direkte manuelle Modifikation im Cluster (Reduktion der Replikate auf 0 via `kubectl`) widerspricht dem in Git deklarierten Sollzustand (`kustomize/overlays/aws/patch-replicas.yaml: replicas=2`). Argo CD detektiert diesen Configuration Drift und erzwingt über die automatisierte Self-Heal-Reconciliation den Sollzustand innerhalb von 30 Sekunden.
- **Auslöser:** `kubectl scale deployment resilience-lab --replicas=0 -n default`

---

## 2. Gemessener Zeitablauf

| Zeitpunkt | Status Argo CD | Soll-Replikate | Ist-Replikate (Ready) | Beschreibung |
|---|---|---|---|---|
| **$t_0 = 0,0\text{ s}$** | `Synced` | 2 | 2 | Ausgangszustand vor Störung |
| **$t_1 = 0,1\text{ s}$** | `Synced` | 0 | 0 | Manuelle Skalierung auf 0 abgesetzt |
| **$t_2 = 2,6\text{ s}$** | **`OutOfSync`** | 0 | 0 | Argo CD erkennt Abweichung von Git |
| **$t_3 = 4,7\text{ s}$** | `Synced` | 2 | 0 | Self-Heal triggert Rollout zurück auf 2 |
| **$t_4 = 11,3\text{ s}$** | `Synced` | 2 | **2** | Beide Pods gestartet und `1/1 Ready` |

---

## 3. Zentrale Kennzahlen

- **Drift-Erkennungszeit ($t_{\text{detect}}$):** **2,58 Sekunden**
- **Wiederherstellungszeit ($\text{MTTR}$):** **11,28 Sekunden**
- **Erfolgsquote:** **100 % (Vollständig automatisiert ohne menschlichen Eingriff)**

---

## 4. Fazit für die Projektarbeit

Das Experiment liefert den empirischen Beweis für den Nutzen von GitOps gegenüber herkömmlichem manuellem Betriebsaufwand:
Unautorisierte oder versehentliche Änderungen am Produktivcluster werden in Echtzeit erkannt und binnen 11 Sekunden autonom korrigiert. Der Sollzustand im Git-Repository bleibt die verbindliche Wahrheit (*Single Source of Truth*).
