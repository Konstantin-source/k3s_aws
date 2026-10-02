#!/usr/bin/env python3
# experiment 2: fehlerhaftes deployment und git revert
import time
import json
import urllib.request
import urllib.error
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

TARGET_URL = "http://63.176.27.134/api/info"
KUBECONFIG = "./kubeconfig-aws.yaml"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def send_req(url):
    start = time.perf_counter()
    status_code = 0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Exp2-Tester/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            status_code = resp.status
    except Exception:
        status_code = 0
    return {
        "status": status_code,
        "duration_ms": (time.perf_counter() - start) * 1000.0
    }

def main():
    print("=== Starte Experiment 2: Fehlerhaftes Deployment & Git Revert ===")
    
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

    # 3. Hintergrundtraffic messen während das fehlerhafte Deployment ansteht
    print("\n[Schritt 2] Beobachte Rolling Update & messe Erreichbarkeit unter Last (20s)...")
    traffic_results = []
    end_time = time.time() + 20
    with ThreadPoolExecutor(max_workers=20) as executor:
        while time.time() < end_time:
            futures = [executor.submit(send_req, TARGET_URL) for _ in range(10)]
            time.sleep(1.0)
            for f in futures:
                res = f.result()
                traffic_results.append(res)
                print("." if res["status"] == 200 else "X", end="", flush=True)

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
    for i in range(60):
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
        "commits": {
            "initial": initial_commit,
            "revert": revert_commit
        },
        "traffic_during_bad_rollout": {
            "total_requests": len(traffic_results),
            "successful_requests": success_count,
            "failed_requests": failed_count,
            "error_rate_percent": round((failed_count / len(traffic_results)) * 100, 2) if traffic_results else 0
        },
        "recovery_time_seconds": round((t_recovered - t_revert) if t_recovered else 60.0, 2)
    }

    with open("experiments/results/exp2-bad-deploy.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nErgebnis gespeichert in experiments/results/exp2-bad-deploy.json")
    print(f"Fehlerrate waehrend fehlerhaftem Rollout: {result['traffic_during_bad_rollout']['error_rate_percent']}%")
    print(f"Wiederherstellungszeit nach Git-Revert: {result['recovery_time_seconds']}s")

if __name__ == "__main__":
    main()
