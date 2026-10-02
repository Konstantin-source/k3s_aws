#!/usr/bin/env python3
"""
Experiment 3: Drift Simulation und Self-Heal Messung
Erfasst sekündliche Zustandsdaten (Sync-Status, Desired vs. Ready Replicas) für Stufendiagramme.
"""
import time
import json
import csv
import subprocess
import os
from datetime import datetime, timezone

KUBECONFIG = "./kubeconfig-aws.yaml"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

def get_app_status():
    sync = run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get application -n argocd resilience-lab -o jsonpath="{{.status.sync.status}}"')
    health = run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get application -n argocd resilience-lab -o jsonpath="{{.status.health.status}}"')
    return sync, health

def get_replicas():
    spec = run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get deployment resilience-lab -n default -o jsonpath="{{.spec.replicas}}"')
    ready = run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get deployment resilience-lab -n default -o jsonpath="{{.status.readyReplicas}}"')
    return spec if spec else "0", ready if ready else "0"

def run_experiment():
    print("=== Starte Experiment 3: Konfigurationsdrift & Self-Heal ===")
    sync_init, health_init = get_app_status()
    print(f"Ausgangszustand: Sync={sync_init}, Health={health_init}")

    log_timeline = []
    timeseries_data = []
    
    t0 = time.time()
    log_timeline.append({"event": "drift_triggered", "timestamp": t0, "detail": "Skalierung auf 0 Replikate"})
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Manuelle Modifikation: replicas=0...")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=0 -n default")

    t_drift_detected = None
    t_repaired = None
    
    # 30 Sekunden mit 0.5s Schritten für glatte Zeitreihe
    for step in range(60):
        time.sleep(0.5)
        curr_time = time.time()
        elapsed = round(curr_time - t0, 1)

        sync, health = get_app_status()
        spec_rep, ready_rep = get_replicas()

        try:
            ready_int = int(ready_rep)
        except ValueError:
            ready_int = 0
        try:
            spec_int = int(spec_rep)
        except ValueError:
            spec_int = 0

        timeseries_data.append({
            "elapsed_s": elapsed,
            "sync_status": sync,
            "desired_replicas": spec_int,
            "ready_replicas": ready_int
        })

        if sync == "OutOfSync" and not t_drift_detected:
            t_drift_detected = curr_time
            log_timeline.append({"event": "drift_detected_by_argocd", "timestamp": curr_time, "elapsed_s": elapsed})
            print(f"  -> [t={elapsed}s] OutOfSync erkannt durch Argo CD!")

        if spec_int == 2 and ready_int == 2 and not t_repaired and t_drift_detected:
            t_repaired = curr_time
            log_timeline.append({"event": "fully_reconciled", "timestamp": curr_time, "elapsed_s": elapsed})
            print(f"  -> [t={elapsed}s] Vollstaendig wiederhergestellt via Self-Heal!")

        if elapsed > 25.0 and t_repaired:
            break

    total_duration = round((t_repaired - t0) if t_repaired else 30.0, 2)
    detection_time = round((t_drift_detected - t0) if t_drift_detected else 0.0, 2)

    # Export CSV
    csv_filename = "experiments/results/exp3-timeseries.csv"
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["elapsed_s", "sync_status", "desired_replicas", "ready_replicas"])
        writer.writeheader()
        writer.writerows(timeseries_data)

    result = {
        "experiment": "Experiment 3 - Konfigurationsabweichung und Self-Heal",
        "date_iso": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "initial_state": {"sync": sync_init, "health": health_init},
            "detection_duration_seconds": detection_time,
            "total_recovery_duration_seconds": total_duration,
            "success": t_repaired is not None
        },
        "timeline": log_timeline,
        "timeseries_file": csv_filename
    }

    output_path = "experiments/results/exp3-config-drift.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nErgebnis gespeichert in: {output_path} und {csv_filename}")
    print(f"Erkennungszeit: {detection_time}s | Gesamte Erholzeit (MTTR): {total_duration}s")

if __name__ == "__main__":
    run_experiment()
