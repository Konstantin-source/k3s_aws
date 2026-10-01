# Vollständiger Abbau & Kostenkontrolle (Teardown Guide)

Um zu verhindern, dass nach Versuchsende unbeabsichtigt Kosten auf AWS entstehen, ist diese Abbauprozedur auszuführen.

---

## 1. Automatisch über Terraform abbauen

```bash
cd terraform
terraform destroy -auto-approve
```

---

## 2. Manuelle Verifikation auf verbleibende Kostenressourcen

Führe nach dem Abbau folgende Prüfungen durch (via AWS CLI oder AWS Web-Konsole):

### A. Laufende EC2-Instanzen prüfen
```bash
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running,pending" \
  --query "Reservations[*].Instances[*].[InstanceId,InstanceType,Tags]" \
  --output table
```
*Erwartung: Keine Instanzen mit Projekt-Tag.*

### B. Nicht freigegebene Elastic IPs prüfen (Nicht zugeordnete EIPs kosten Geld!)
```bash
aws ec2 describe-addresses \
  --query "Addresses[*].[PublicIp,AllocationId,AssociationId]" \
  --output table
```
*Erwartung: Liste ist leer.*

### C. Herrenlose EBS-Volumes (Unattached Volumes)
```bash
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query "Volumes[*].[VolumeId,Size,CreateTime]" \
  --output table
```
*Erwartung: Keine Volumes mit Status `available`.*
