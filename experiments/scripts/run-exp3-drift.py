#!/usr/bin/env python3
# experiment 3: drift simulation und self-heal messung
import time
import json
import subprocess
from datetime import datetime, timezone

KUBECONFIG = "./kubeconfig-aws.yaml"
COMMIT_SHA = "07a858dac10fe5e76bec13440a743e7a9331bd21"
IMAGE_TAG = "1.0.0"

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
    return spec, ready

def run_experiment():
    print("=== Starte Experiment 3: Konfigurationsdrift & Self-Heal ===")
    sync_init, health_init = get_app_status()
    print(f"Ausgangszustand: Sync={sync_init}, Health={health_init}")

    log_timeline = []
    
    t0 = time.time()
    log_timeline.append({"event": "drift_triggered", "timestamp": t0, "detail": "Skalierung auf 0 Replikate"})
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Manuelle Modifikation: replicas=0...")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=0 -n default")

    t_drift_detected = None
    t_repaired = None
    
    # max 120 sekunden beobachten
    for i in range(120):
        time.sleep(1)
        sync, health = get_app_status()
        spec_rep, ready_rep = get_replicas()
        curr_time = time.time()
        elapsed = round(curr_time - t0, 1)

        print(f"  t+{elapsed}s: Sync={sync}, SpecReplicas={spec_rep}, ReadyReplicas={ready_rep}")

        if sync == "OutOfSync" and not t_drift_detected:
            t_drift_detected = curr_time
            log_timeline.append({"event": "drift_detected_by_argocd", "timestamp": curr_time, "elapsed_s": elapsed})
            print(f"  -> OutOfSync erkannt nach {elapsed}s!")

        if spec_rep == "2" and ready_rep == "2":
            t_repaired = curr_time
            log_timeline.append({"event": "fully_reconciled", "timestamp": curr_time, "elapsed_s": elapsed})
            print(f"  -> Vollstaendig wiederhergestellt via Self-Heal nach {elapsed}s!")
            break

    total_duration = round((t_repaired - t0) if t_repaired else 120.0, 2)
    detection_time = round((t_drift_detected - t0) if t_drift_detected else 0.0, 2)

    events_raw = run_cmd(f"kubectl --kubeconfig {KUBECONFIG} get events -n default --sort-by='.lastTimestamp'")

    result = {
        "experiment": "Experiment 3 - Konfigurationsabweichung und Self-Heal",
        "date_iso": datetime.now(timezone.utc).isoformat(),
        "git_commit": COMMIT_SHA,
        "image_version": IMAGE_TAG,
        "cluster": "k3s on AWS EC2 (eu-central-1)",
        "metrics": {
            "initial_state": {"sync": sync_init, "health": health_init},
            "detection_duration_seconds": detection_time,
            "total_recovery_duration_seconds": total_duration,
            "success": t_repaired is not None
        },
        "timeline": log_timeline,
        "cluster_events": events_raw
    }

    output_path = "experiments/results/exp3-config-drift.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nErgebnis gespeichert in: {output_path}")
    print(f"Erkennungszeit: {detection_time}s | Gesamte Erholzeit: {total_duration}s")

if __name__ == "__main__":
    run_experiment()
