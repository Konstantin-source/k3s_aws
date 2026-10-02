#!/usr/bin/env python3
"""
Experiment 1: Prozessabsturz unter kontinuierlicher Last (Vergleich 1 Pod vs. 2 Pods)
Erfasst sekündliche Zeitreihendaten für direkte Visualisierung (Liniendiagramme).
"""
import time
import json
import csv
import urllib.request
import urllib.error
import subprocess
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

def get_eip():
    try:
        res = subprocess.run("terraform -chdir=terraform output -raw public_ip", shell=True, capture_output=True, text=True)
        ip = res.stdout.strip()
        if ip and "." in ip:
            return ip
    except Exception:
        pass
    return "3.64.33.245"

KUBECONFIG = "./kubeconfig-aws.yaml"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def send_req(url):
    start = time.perf_counter()
    status_code = 0
    served_by = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Exp1-HighRes/2.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            status_code = resp.status
            served_by = resp.headers.get("X-Served-By-Pod")
    except urllib.error.HTTPError as e:
        status_code = e.code
    except Exception:
        status_code = 0
    duration_ms = (time.perf_counter() - start) * 1000.0
    return {
        "status": status_code,
        "duration_ms": duration_ms,
        "pod": served_by
    }

def run_test_run(label, target_url, crash_url, csv_filename, duration=40, rps=40, crash_at=15):
    print(f"\n=======================================================")
    print(f"--- Testlauf: {label} ---")
    print(f"Dauer: {duration}s | Rate: {rps} Req/s | Crash bei t={crash_at}s")
    print(f"=======================================================")
    
    all_results = []
    timeseries_buckets = []
    crashed = False
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=rps * 2) as executor:
        for current_second in range(duration):
            sec_start = time.time()
            t_elapsed = sec_start - start_time

            # Trigger Crash at target time
            if not crashed and t_elapsed >= crash_at:
                try:
                    req_crash = urllib.request.Request(crash_url, method="POST")
                    urllib.request.urlopen(req_crash, timeout=2.0)
                    print(f"\n[CRASH] [t={round(t_elapsed, 1)}s] Crash-Signal forciert via {crash_url}!")
                except Exception as e:
                    print(f"\n[CRASH] [t={round(t_elapsed, 1)}s] Crash-Signal ausgeloest (Antwort: {e})")
                crashed = True

            # Send batch of requests for this second
            futures = [executor.submit(send_req, target_url) for _ in range(rps)]
            
            # Sleep until the second boundary
            elapsed_in_sec = time.time() - sec_start
            if elapsed_in_sec < 1.0:
                time.sleep(1.0 - elapsed_in_sec)

            # Collect results for this bucket
            sec_results = [f.result() for f in futures]
            all_results.extend(sec_results)

            sec_success = sum(1 for r in sec_results if r["status"] == 200)
            sec_failed = rps - sec_success
            sec_durations = sorted([r["duration_ms"] for r in sec_results if r["status"] == 200])

            p50 = sec_durations[int(len(sec_durations) * 0.5)] if sec_durations else 0.0
            p95 = sec_durations[int(len(sec_durations) * 0.95)] if sec_durations else 0.0
            sec_err_rate = round((sec_failed / rps) * 100.0, 2)

            bucket = {
                "second": current_second,
                "requests": rps,
                "success": sec_success,
                "failed": sec_failed,
                "error_rate": sec_err_rate,
                "p50_ms": round(p50, 1),
                "p95_ms": round(p95, 1)
            }
            timeseries_buckets.append(bucket)

            status_char = "OK" if sec_failed == 0 else f"ERR({sec_failed})"
            print(f"t={current_second:02d}s: {sec_success:2d}/{rps} OK | p50={p50:5.1f}ms | {status_char}")

    # Write Time-Series CSV
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["second", "requests", "success", "failed", "error_rate", "p50_ms", "p95_ms"])
        writer.writeheader()
        writer.writerows(timeseries_buckets)
    print(f"-> Zeitreihendaten exportiert nach: {csv_filename}")

    # Calculate overall summary
    total = len(all_results)
    total_success = sum(1 for r in all_results if r["status"] == 200)
    total_failed = total - total_success
    all_valid_durations = sorted([r["duration_ms"] for r in all_results if r["status"] == 200])

    tot_p50 = all_valid_durations[int(len(all_valid_durations) * 0.5)] if all_valid_durations else 0
    tot_p95 = all_valid_durations[int(len(all_valid_durations) * 0.95)] if all_valid_durations else 0

    summary = {
        "label": label,
        "total_requests": total,
        "successful_requests": total_success,
        "failed_requests": total_failed,
        "error_rate_percent": round((total_failed / total) * 100, 2) if total > 0 else 0,
        "availability_percent": round((total_success / total) * 100, 2) if total > 0 else 0,
        "latency_p50_ms": round(tot_p50, 2),
        "latency_p95_ms": round(tot_p95, 2),
        "timeseries_file": csv_filename
    }
    return summary

def main():
    target_ip = get_eip()
    target_url = f"http://{target_ip}/api/info"
    crash_url = f"http://{target_ip}/lab/crash"

    print(f"=== Experiment 1: Hochfrequenz-Messung & Zeitreihenanalyse ===")
    print(f"Ziel-Host: {target_ip}")
    print(f"Target URL: {target_url}")

    # 1. Verbesserte Konfiguration (2 Replicas)
    print("\n[Schritt 1] Stelle 2 Replicas sicher...")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=2 -n default")
    time.sleep(12)
    summary_2pods = run_test_run(
        label="2 Replicas (Verbesserte Konfiguration)",
        target_url=target_url,
        crash_url=crash_url,
        csv_filename="experiments/results/exp1-timeseries-2pods.csv",
        duration=40,
        rps=40,
        crash_at=15
    )

    # 2. Basiskonfiguration (1 Replica)
    print("\n[Schritt 2] Skaliere auf 1 Pod fuer Basiskonfiguration...")
    # Argo CD Auto-Sync pausieren fuer Baseline
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} patch app resilience-lab -n argocd --type=merge -p '{{\"spec\":{{\"syncPolicy\":null}}}}'")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=1 -n default")
    time.sleep(12)
    summary_1pod = run_test_run(
        label="1 Replica (Basiskonfiguration)",
        target_url=target_url,
        crash_url=crash_url,
        csv_filename="experiments/results/exp1-timeseries-1pod.csv",
        duration=40,
        rps=40,
        crash_at=15
    )

    # Argo CD Auto-Sync wiederherstellen
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} patch app resilience-lab -n argocd --type=merge -p '{{\"spec\":{{\"syncPolicy\":{{\"automated\":{{\"prune\":true,\"selfHeal\":true}}}}}}}}'")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=2 -n default")

    overall = {
        "experiment": "Experiment 1 - Prozessabsturz (1 Pod vs 2 Pods)",
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "target_ip": target_ip,
        "parameters": {
            "duration_seconds": 40,
            "requests_per_second": 40,
            "total_requests_per_run": 1600,
            "crash_at_second": 15
        },
        "comparison": {
            "single_replica_baseline": summary_1pod,
            "multi_replica_improved": summary_2pods
        }
    }

    with open("experiments/results/exp1-crash.json", "w") as f:
        json.dump(overall, f, indent=2)
    print(f"\n=======================================================")
    print("Ergebnisse erfolgreich gespeichert in:")
    print("  - experiments/results/exp1-crash.json")
    print("  - experiments/results/exp1-timeseries-1pod.csv")
    print("  - experiments/results/exp1-timeseries-2pods.csv")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
