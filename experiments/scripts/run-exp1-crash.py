#!/usr/bin/env python3
# experiment 1: prozessabsturz vergleich 1 pod vs 2 pods
import time
import json
import urllib.request
import urllib.error
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

TARGET_URL = "http://63.176.27.134/api/info"
CRASH_URL = "http://63.176.27.134/lab/crash"
RESET_URL = "http://63.176.27.134/lab/reset"
KUBECONFIG = "./kubeconfig-aws.yaml"
COMMIT_SHA = "9a3468f"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def send_req(url):
    start = time.perf_counter()
    status_code = 0
    served_by = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Exp1-Tester/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            status_code = resp.status
            served_by = resp.headers.get("X-Served-By-Pod")
    except urllib.error.HTTPError as e:
        status_code = e.code
    except Exception:
        status_code = 0
    duration_ms = (time.perf_counter() - start) * 1000.0
    return {
        "timestamp": time.time(),
        "status": status_code,
        "duration_ms": duration_ms,
        "pod": served_by
    }

def run_test_run(label, duration=35, rps=15, crash_at=12):
    print(f"\n--- Testlauf: {label} ({duration}s, {rps} rps, crash bei t+{crash_at}s) ---")
    results = []
    end_time = time.time() + duration
    start_time = time.time()
    crashed = False

    with ThreadPoolExecutor(max_workers=rps * 2) as executor:
        while time.time() < end_time:
            t_curr = time.time() - start_time
            if not crashed and t_curr >= crash_at:
                try:
                    req_crash = urllib.request.Request(CRASH_URL, method="POST")
                    urllib.request.urlopen(req_crash, timeout=2.0)
                    print(f"\n💥 Crash-Signal abgesetzt bei t={round(t_curr, 1)}s!")
                except Exception as e:
                    print(f"\nCrash-Signal geworfen: {e}")
                crashed = True

            futures = [executor.submit(send_req, TARGET_URL) for _ in range(rps)]
            time.sleep(1.0)
            for f in futures:
                res = f.result()
                results.append(res)
                print("." if res["status"] == 200 else "X", end="", flush=True)

    total = len(results)
    success = sum(1 for r in results if r["status"] == 200)
    failed = total - success
    valid_durations = sorted([r["duration_ms"] for r in results if r["status"] == 200])

    p50 = valid_durations[int(len(valid_durations) * 0.5)] if valid_durations else 0
    p95 = valid_durations[int(len(valid_durations) * 0.95)] if valid_durations else 0

    summary = {
        "label": label,
        "total_requests": total,
        "successful_requests": success,
        "failed_requests": failed,
        "error_rate_percent": round((failed / total) * 100, 2) if total > 0 else 0,
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95, 2),
    }
    print(f"\nErgebnis für {label}: {json.dumps(summary, indent=2)}")
    return summary, results

def main():
    print("=== Starte Experiment 1: Prozessabsturz (Vergleich 1 Pod vs. 2 Pods) ===")
    
    # 1. Verbesserte Konfiguration (2 Replicas)
    print("\n[Schritt 1] Stelle 2 Replicas sicher...")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=2 -n default")
    time.sleep(10)
    summary_2pods, raw_2pods = run_test_run("2 Replicas (Verbesserte Konfiguration)")

    # 2. Basiskonfiguration (1 Replica)
    print("\n[Schritt 2] Skaliere auf 1 Pod fuer Basiskonfiguration...")
    # argocd auto-sync temporaer pausieren damit er 1 replica fuer den test erlaubt
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} patch app resilience-lab -n argocd --type=merge -p '{{\"spec\":{{\"syncPolicy\":null}}}}'")
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} scale deployment resilience-lab --replicas=1 -n default")
    time.sleep(10)
    summary_1pod, raw_1pod = run_test_run("1 Replica (Basiskonfiguration)")

    # argo cd auto-sync wiederherstellen
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} patch app resilience-lab -n argocd --type=merge -p '{{\"spec\":{{\"syncPolicy\":{{\"automated\":{{\"prune\":true,\"selfHeal\":true}}}}}}}}'")

    overall = {
        "experiment": "Experiment 1 - Prozessabsturz (1 Pod vs 2 Pods)",
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "git_commit": COMMIT_SHA,
        "comparison": {
            "single_replica_baseline": summary_1pod,
            "multi_replica_improved": summary_2pods
        }
    }

    with open("experiments/results/exp1-crash.json", "w") as f:
        json.dump(overall, f, indent=2)
    print("\nGespeichert in: experiments/results/exp1-crash.json")

if __name__ == "__main__":
    main()
