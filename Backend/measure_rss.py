import sys
import os
import subprocess
import time

# Ensure Backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main

def get_current_rss_mb():
    pid = os.getpid()
    cmd = ["powershell", "-NoProfile", "-Command", f"([System.Diagnostics.Process]::GetProcessById({pid})).WorkingSet64 / 1MB"]
    out = subprocess.check_output(cmd, text=True).strip()
    return round(float(out), 2)

def check_no_engine_imports():
    prohibited = ["pandas", "sklearn", "scipy", "numpy"]
    loaded = [mod for mod in prohibited if mod in sys.modules]
    return loaded

def run_benchmark():
    print("=" * 60)
    print("      RESTOCKIQ BACKEND RSS MEMORY BENCHMARK (3 RUNS)")
    print("=" * 60)

    # 1. Prohibited module check
    loaded_prohibited = check_no_engine_imports()
    print(f"\n[1] Prohibited Engine Module Check (pandas / sklearn / numpy):")
    if loaded_prohibited:
        print(f"  [FAIL] Detected heavy engine modules in FastAPI process: {loaded_prohibited}")
    else:
        print(f"  [PASS] ZERO prohibited engine modules imported in FastAPI process!")

    client = TestClient(main.app)

    # 2. Run 3 measurement cycles
    results = []
    for run_idx in range(1, 4):
        idle_rss = get_current_rss_mb()
        # Fire 20 requests
        for i in range(20):
            res = client.get("/health")
            assert res.status_code == 200

        after_rss = get_current_rss_mb()
        delta = round(after_rss - idle_rss, 2)
        results.append({
            "run": run_idx,
            "idle_rss": idle_rss,
            "after_20_reqs": after_rss,
            "delta": delta,
        })
        print(f"  Run {run_idx}: Idle RSS = {idle_rss} MB | After 20 Requests = {after_rss} MB | Delta = {delta:+} MB")
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("                     BENCHMARK SUMMARY")
    print("=" * 60)
    avg_idle = round(sum(r["idle_rss"] for r in results) / len(results), 2)
    avg_after = round(sum(r["after_20_reqs"] for r in results) / len(results), 2)
    print(f"Average Idle RSS:           {avg_idle} MB")
    print(f"Average After 20 Requests:  {avg_after} MB")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
