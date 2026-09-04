import json
import time
import requests

RESULTS_PATH = "eval_results.json"
AGENT_URL = "https://ingredient-agent-247055277121.us-central1.run.app/analyze"
DELAY_SECONDS = 30  # extra generous, since these 5 already proved they sit at the edge

with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

degraded_entries = [
    e for e in results
    if e.get("agent_response", {}).get("_details", {}).get("extraction_error")
]

print(f"Re-running {len(degraded_entries)} degraded products...\n")

for i, entry in enumerate(degraded_entries):
    image_path = entry["image"]
    with open(image_path, "rb") as f:
        files = {"image": f}
        data = {"product_type": entry["product_type"]}
        try:
            resp = requests.post(AGENT_URL, files=files, data=data, timeout=60)
            resp.raise_for_status()
            new_response = resp.json()
            still_degraded = bool(new_response.get("_details", {}).get("extraction_error"))
            entry["agent_response"] = new_response
            print(f"{image_path}: {'still degraded' if still_degraded else 'CLEAN — recovered'}")
        except requests.RequestException as e:
            print(f"{image_path}: request failed ({e})")

    if i < len(degraded_entries) - 1:
        time.sleep(DELAY_SECONDS)

with open(RESULTS_PATH, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nUpdated {RESULTS_PATH} with re-run results.")