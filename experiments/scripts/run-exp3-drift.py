#!/usr/bin/env python3
# experiment 3: drift (replicas=0) und self-heal, enge polling-schleife
import time
import json
import csv
import subprocess
import os
from datetime import datetime, timezone

KUBECONFIG = "./kubeconfig-aws.yaml"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def get_state():
    # ein einziger kubectl-aufruf: spec|ready
    out = run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get deployment resilience-lab -n default -o jsonpath="{{.spec.replicas}}|{{.status.readyReplicas}}"')
    spec, _, ready = out.partition("|")
    return int(spec or 0), int(ready or 0)

def get_sync():
    return run_cmd(f'kubectl --kubeconfig {KUBECONFIG} get application -n argocd resilience-lab -o jsonpath="{{.status.sync.status}}"')

def main():
    print("=== Experiment 3: Konfigurationsdrift & Self-Heal ===")
    sync_init = get_sync()
    spec0, ready0 = get_state()
    print(f"Ausgangszustand: Sync={sync_init}, spec={spec0}, ready={ready0}")

    rows = []
    t0 = time.time()
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=0 -n default")
    t_scaled = time.time() - t0
    print(f"scale auf 0 abgesetzt nach {t_scaled:.2f}s")

    seen_zero = False
    t_reverted = None   # spec wieder 2 (argo hat die drift korrigiert)
    t_repaired = None   # ready wieder 2
    while time.time() - t0 < 90:
        spec, ready = get_state()
        el = round(time.time() - t0, 2)
        rows.append({"elapsed_s": el, "desired_replicas": spec, "ready_replicas": ready})
        print(f"t={el:6.2f}s spec={spec} ready={ready}")
        if spec == 0:
            seen_zero = True
        if seen_zero and spec == 2 and t_reverted is None:
            t_reverted = el
        if t_reverted is not None and ready == 2:
            t_repaired = el
            break
        if not seen_zero and spec == 2 and ready == 2 and el > 5:
            break  # drift wurde nie sichtbar

    csv_path = "experiments/results/exp3-timeseries.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["elapsed_s", "desired_replicas", "ready_replicas"])
        w.writeheader()
        w.writerows(rows)

    result = {
        "experiment": "Experiment 3 - Konfigurationsabweichung und Self-Heal",
        "date_iso": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "initial_sync": sync_init,
            "scale_command_duration_s": round(t_scaled, 2),
            "drift_visible": seen_zero,
            "argo_revert_s": t_reverted,
            "full_recovery_s": t_repaired,
            "poll_interval_note": "ca. 0.7 s je kubectl-aufruf",
            "success": t_repaired is not None
        },
        "timeseries_file": csv_path
    }
    with open("experiments/results/exp3-config-drift.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Argo-Revert nach {t_reverted}s | volle Wiederherstellung nach {t_repaired}s")

if __name__ == "__main__":
    main()
