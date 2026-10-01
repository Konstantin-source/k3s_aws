# AWS Kostenschätzung: k3s auf EC2

> **Gültig für Region:** `eu-central-1` (Frankfurt)  
> **Budgetrahmen:** max. 100 EUR Startguthaben  
> **Geplante Laufzeit:** Gezielte Testphasen (Stunden bis wenige Tage), maximal 1 Monat

---

## 1. Detaillierte Kostenaufstellung

| Ressource | Spezifikation | Preis pro Einheit | Kosten / 24h | Kosten / 30 Tage (730h) |
|---|---|---|---|---|
| **EC2-Instanz** | `t3.small` (2 vCPU, 2 GB RAM, On-Demand) | 0,0208 USD / h | 0,50 USD | ~15,18 USD |
| **EBS Speicher** | 30 GB gp3 Root-Volume | 0,08 USD / GB-Monat | 0,08 USD | ~2,40 USD |
| **Elastic IP** | 1 feste IPv4-Adresse (zugewiesen an laufende EC2) | 0,005 USD / h | 0,12 USD | ~3,65 USD |
| **VPC & Subnetze** | 1 VPC, 1 Public Subnet, Internet Gateway | 0,00 USD (kostenfrei) | 0,00 USD | 0,00 USD |
| **Security Groups** | Stateful Firewall-Regeln | 0,00 USD (kostenfrei) | 0,00 USD | 0,00 USD |
| **Datenübertragung** | Outbound Traffic (Messungen / Web-UI < 10 GB) | ~0,09 USD / GB (erste 100 GB oft frei) | ~0,05 USD | ~1,00 USD |
| **GESAMT** | | | **~0,75 USD / Tag** | **~22,23 USD / Monat** |

---

## 2. Vergleich zur Amazon EKS-Variante

| Kriterium | k3s auf EC2 (`t3.small`) | Amazon EKS (Managed) |
|---|---|---|
| Control Plane Gebühr | **0,00 USD** (lokal auf EC2) | **73,00 USD** (0,10 USD / h fix) |
| Worker Nodes | Inklusive auf derselben VM | mind. 2× `t3.medium` (~60 USD) |
| Load Balancer / NAT | Traefik (integriert, 0 USD) | ALB / NLB (~16 USD) + NAT Gateway (~32 USD) |
| **Monatssumme** | **~22 USD (~20 EUR)** | **~185 USD (~170 EUR)** |
| **Reichweite mit 100 EUR** | **> 4 Monate** | **< 2,5 Wochen** |

---

## 3. Spar- & Sicherheitsstrategie

1. **Kein Dauerbetrieb erforderlich:** Die Infrastruktur wird nur für die Durchführung der Experimente via `terraform apply` hochgefahren und nach Abschluss der Messungen am selben Tag mit `terraform destroy` vollständig abgebaut.
   - 10 Stunden Testbetrieb kosten lediglich **ca. 0,31 USD**.
2. **Kostenfreigabe:** Erst nach Prüfung dieses Dokuments wird Terraform gegen das AWS-Konto ausgeführt.
3. **Abbau-Verifikation:** Nach jedem Destroy wird mit dem Prüfskript `docs/teardown.md` verifiziert, dass keine herrenlosen Volumes oder Elastic IPs Kosten verursachen.
