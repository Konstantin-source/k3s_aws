#!/usr/bin/env python3
"""
Experiment 2: Fehlerhaftes Deployment und Git-Revert
Erfasst sekündliche Zeitreihendaten während des Rollouts zur Verifikation von 0% Fehlerrate.
"""
import time
import json
import csv
import urllib.request
import urllib.error
import subprocess
import os
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
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Exp2-HighRes/2.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            status_code = resp.status
    except Exception:
        status_code = 0
    return {
        "status": status_code,
        "duration_ms": (time.perf_counter() - start) * 1000.0
    }

def main():
    target_ip = get_eip()
    target_url = f"http://{target_ip}/api/info"

    print("=== Starte Experiment 2: Fehlerhaftes Deployment & Git Revert ===")
    print(f"Ziel-Host: {target_ip}")
    
    # 1. Ausgangszustand
    initial_commit = run_cmd("git rev-parse HEAD")
    print(f"Ausgangs-Commit: {initial_commit}")

    # 2. Fehlerhafte Readiness-Probe in deployment.yaml einbauen
    dep_path = "kustomize/base/deployment.yaml"
    with open(dep_path, "r") as f:
        content = f.read()

    bad_content = content.replace("path: /health/ready", "path: /health/broken-endpoint-404")
    with open(dep_path, "w") as f:
        f.write(bad_content)

    print("\n[Schritt 1] Pushe fehlerhaftes Deployment nach Git...")
    run_cmd('git commit -am "test(exp2): deploy release with broken readiness probe" && git push origin main')
    t_push_bad = time.time()

    # Argo CD Refresh triggern
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} annotate application -n argocd resilience-lab argocd.argoproj.io/refresh=normal --overwrite")

    # 3. Hintergrundtraffic messen während das fehlerhafte Deployment ansteht (25s @ 25 Req/s = 625 Requests)
    print("\n[Schritt 2] Beobachte Rolling Update & messe Erreichbarkeit unter Last (25s, 25 Req/s)...")
    traffic_results = []
    timeseries_buckets = []
    rps = 25
    duration = 25
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=rps * 2) as executor:
        for current_second in range(duration):
            sec_start = time.time()
            futures = [executor.submit(send_req, target_url) for _ in range(rps)]
            
            elapsed_in_sec = time.time() - sec_start
            if elapsed_in_sec < 1.0:
                time.sleep(1.0 - elapsed_in_sec)

            sec_results = [f.result() for f in futures]
            traffic_results.extend(sec_results)

            sec_success = sum(1 for r in sec_results if r["status"] == 200)
            sec_failed = rps - sec_success
            sec_durations = sorted([r["duration_ms"] for r in sec_results if r["status"] == 200])
            p50 = sec_durations[int(len(sec_durations) * 0.5)] if sec_durations else 0.0
            p95 = sec_durations[int(len(sec_durations) * 0.95)] if sec_durations else 0.0

            timeseries_buckets.append({
                "second": current_second,
                "requests": rps,
                "success": sec_success,
                "failed": sec_failed,
                "error_rate": round((sec_failed / rps) * 100.0, 2),
                "p50_ms": round(p50, 1),
                "p95_ms": round(p95, 1)
            })
            print(f"t={current_second:02d}s: {sec_success:2d}/{rps} OK | p50={p50:5.1f}ms")

    # Export CSV
    csv_filename = "experiments/results/exp2-timeseries.csv"
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["second", "requests", "success", "failed", "error_rate", "p50_ms", "p95_ms"])
        writer.writeheader()
        writer.writerows(timeseries_buckets)

    pods_during_rollout = run_cmd(f"kubectl --kubeconfig {KUBECONFIG} get pods -n default")
    print(f"\nPods waehrend Rollout:\n{pods_during_rollout}")

    # 4. Git Revert durchführen
    print("\n[Schritt 3] Fuehre Git Revert durch...")
    run_cmd("git revert HEAD --no-edit && git push origin main")
    t_revert = time.time()
    revert_commit = run_cmd("git rev-parse HEAD")
    print(f"Revert-Commit gepusht: {revert_commit}")

    # Argo CD Refresh triggern
    run_cmd(f"kubectl --kubeconfig {KUBECONFIG} annotate application -n argocd resilience-lab argocd.argoproj.io/refresh=normal --overwrite")

    # 5. Warten bis alle Pods wieder healthy sind
    print("\n[Schritt 4] Warte auf GitOps Revert-Synchronisation...")
    t_recovered = None
    for i in range(90):
        time.sleep(1)
        pods = run_cmd(f"kubectl --kubeconfig {KUBECONFIG} get pods -n default")
        app_health = run_cmd(f"kubectl --kubeconfig {KUBECONFIG} get application -n argocd resilience-lab -o jsonpath=\"{{.status.health.status}}\"")
        if "Terminating" not in pods and app_health == "Healthy":
            t_recovered = time.time()
            print(f"-> Vollstaendig bereinigt nach {round(t_recovered - t_revert, 1)}s!")
            break

    # Auswertung
    success_count = sum(1 for r in traffic_results if r["status"] == 200)
    failed_count = len(traffic_results) - success_count

    result = {
        "experiment": "Experiment 2 - Fehlerhaftes Deployment und Git Revert",
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "target_ip": target_ip,
        "commits": {
            "initial": initial_commit,
            "revert": revert_commit
        },
        "traffic_during_bad_rollout": {
            "total_requests": len(traffic_results),
            "successful_requests": success_count,
            "failed_requests": failed_count,
            "error_rate_percent": round((failed_count / len(traffic_results)) * 100, 2) if traffic_results else 0,
            "availability_percent": round((success_count / len(traffic_results)) * 100, 2) if traffic_results else 0
        },
        "recovery_time_seconds": round((t_recovered - t_revert) if t_recovered else 60.0, 2),
        "timeseries_file": csv_filename
    }

    with open("experiments/results/exp2-bad-deploy.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nErgebnis gespeichert in experiments/results/exp2-bad-deploy.json")
    print(f"Gesamtanfragen waehrend Rollout: {len(traffic_results)} (100% Erfolg: {success_count})")
    print(f"Wiederherstellungszeit nach Git-Revert: {result['recovery_time_seconds']}s")

if __name__ == "__main__":
    main()
