import json
import time
import requests

DATASET_PATH = "eval_ground_truth.json"
BASE_URL = "https://ingredient-agent-247055277121.us-central1.run.app"
DELAY_SECONDS = 20  # widened after observing 5/6 requests rate-limited at 5s spacing

with open(DATASET_PATH, "r") as f:
    dataset = json.load(f)

print("Sending warm-up request...")
start = time.time()
try:
    requests.get(f"{BASE_URL}/health", timeout=90)
    print(f"Cold start / warm-up time: {time.time() - start:.2f}s\n")
except requests.RequestException as e:
    print(f"Warm-up failed: {e}\n")

warm_latencies = []
degraded_latencies = []

for i, entry in enumerate(dataset):
    image_path = entry["image"]
    with open(image_path, "rb") as f:
        files = {"image": f}
        data = {"product_type": entry["product_type"]}
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=60)
            elapsed = time.time() - start
            resp.raise_for_status()

            body = resp.json()
            is_degraded = bool(body.get("_details", {}).get("extraction_error"))

            if is_degraded:
                degraded_latencies.append(elapsed)
                print(f"{image_path}: {elapsed:.2f}s (DEGRADED -- extraction_error, excluded from main stats)")
            else:
                warm_latencies.append(elapsed)
                print(f"{image_path}: {elapsed:.2f}s")
        except requests.RequestException as e:
            print(f"{image_path}: FAILED ({e})")

    if i < len(dataset) - 1:
        time.sleep(DELAY_SECONDS)

if warm_latencies:
    warm_latencies.sort()
    n = len(warm_latencies)
    print(f"\n--- Warm latency (n={n} full successful requests, container already running) ---")
    print(f"Mean:   {sum(warm_latencies)/n:.2f}s")
    print(f"Median: {warm_latencies[n // 2]:.2f}s")
    print(f"Min:    {min(warm_latencies):.2f}s")
    print(f"Max:    {max(warm_latencies):.2f}s")
    p95_idx = int(n * 0.95) if n >= 20 else n - 1
    print(f"P95:    {warm_latencies[p95_idx]:.2f}s")

if degraded_latencies:
    print(f"\n--- Degraded requests (n={len(degraded_latencies)}) -- excluded above, reported separately ---")
    print(f"These hit extraction_error (rate limit or unparseable output) and returned early;")
    print(f"their latency does not reflect full pipeline execution.")