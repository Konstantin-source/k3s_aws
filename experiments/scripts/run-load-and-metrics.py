#!/usr/bin/env python3
import time
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# einzelner request mit zeitmessung
def send_request(url):
    start = time.perf_counter()
    status_code = 0
    error_msg = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Tester/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            status_code = resp.status
            body = resp.read()
    except urllib.error.HTTPError as e:
        status_code = e.code
    except Exception as e:
        status_code = 0
        error_msg = str(e)

    duration_ms = (time.perf_counter() - start) * 1000.0
    return {
        "timestamp": time.time(),
        "status_code": status_code,
        "duration_ms": duration_ms,
        "error": error_msg
    }

# feuert parallele anfragen und sammelt latenz
def run_benchmark(target_url, duration_seconds=60, rps=10, output_file=None):
    print(f"teste {target_url} ({duration_seconds}s, ~{rps} rps)")
    results = []
    end_time = time.time() + duration_seconds

    with ThreadPoolExecutor(max_workers=rps * 2) as executor:
        while time.time() < end_time:
            futures = [executor.submit(send_request, target_url) for _ in range(rps)]
            time.sleep(1.0)
            for f in futures:
                res = f.result()
                results.append(res)
                # punkt bei erfolg, x bei fehler
                print("." if res["status_code"] == 200 else "X", end="", flush=True)

    print("\nfertig, rechne ergebnisse aus...")
    total = len(results)
    success = sum(1 for r in results if r["status_code"] == 200)
    failed = total - success
    durations = sorted([r["duration_ms"] for r in results if r["status_code"] == 200])

    p50 = durations[int(len(durations) * 0.5)] if durations else 0
    p95 = durations[int(len(durations) * 0.95)] if durations else 0

    summary = {
        "target_url": target_url,
        "total_requests": total,
        "successful": success,
        "failed": failed,
        "error_rate": round((failed / total) * 100, 2) if total > 0 else 0,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
    }

    print(json.dumps(summary, indent=2))

    if output_file:
        with open(output_file, "w") as f:
            json.dump({"summary": summary, "raw": results}, f, indent=2)
        print(f"gespeichert in {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/api/info")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--rps", type=int, default=10)
    parser.add_argument("--output", default="benchmark-results.json")
    args = parser.parse_args()

    run_benchmark(args.url, args.duration, args.rps, args.output)
