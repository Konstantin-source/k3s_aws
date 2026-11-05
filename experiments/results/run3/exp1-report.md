# Evaluationsbericht: Experiment 1 – Prozessabsturz (1 Pod vs. 2 Pods)

> **Datum:** 01.10.2026, 10:03 Uhr (UTC 08:03)  
> **Git-Commit:** `9a3468f`  
> **Cluster:** k3s auf AWS EC2 (`t3.small`, eu-central-1)  
> **Lastprofil:** 15 Requests / Sekunde (insgesamt 525 Anfragen pro Lauf)

---

## 1. Versuchsaufbau & Hypothese

- **Hypothese:** Bei einem forcierten Prozessabsturz führt die Basiskonfiguration (1 Pod) während des Kubelet-Neustarts zu einer vollständigen Nicht-Erreichbarkeit des Services. In der verbesserten Konfiguration (2 Pods) übernimmt die verbleibende Instanz den Datenverkehr, sodass nur die minimalen Anfragen im Flug (in-flight) zum Absturzzeitpunkt scheitern.

---

## 2. Vergleich der Messergebnisse

| Konfiguration | Anfragen Gesamt | Erfolgreich (200 OK) | Fehlgeschlagen | Fehlerrate | Latenz $p_{50}$ | Latenz $p_{95}$ |
|---|---|---|---|---|---|---|
| **Basiskonfiguration (1 Pod)** | 525 | 517 | 8 | **1,52 %** | 50,75 ms | 162,06 ms |
| **Verbesserte Konfiguration (2 Pods)** | 525 | 518 | 7 | **1,33 %** | 55,20 ms | 159,81 ms |

---

## 3. Analyse & Erkenntnisgewinn

1. **Kubelet-Selbstreparatur:** In beiden Szenarien hat das Kubelet den abgestürzten Containerprozess innerhalb von ca. 1–2 Sekunden neu gestartet.
2. **Begrenzung von Multi-Replica:** Mehrere Pods verhindern nicht, dass Anfragen, die *während des exakten Absturzes* im TCP-Handshake waren, abgebrochen werden. Hierfür wären client-seitige Retries bzw. Service-Mesh-Mechanismen notwendig.
3. **Erholungszeit:** Bei 2 Pods stand die Gesamtkapazität sofort wieder zur Verfügung, während bei 1 Pod der Dienst während des Neustarts für kurze Zeit keine neuen Verbindungen akzeptieren konnte.
