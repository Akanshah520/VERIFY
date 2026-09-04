import json
import time
import requests

DATASET_PATH = "eval_ground_truth.json"
AGENT_URL = "https://ingredient-agent-247055277121.us-central1.run.app/analyze"
DELAY_SECONDS = 20  # widened after observing 5/6 requests rate-limited at 5s spacing

with open(DATASET_PATH, "r") as f:
    ground_truth = json.load(f)

for i, entry in enumerate(ground_truth):
    image_path = entry["image"]
    with open(image_path, "rb") as f:
        files = {"image": f}
        data = {"product_type": entry["product_type"]}
        try:
            resp = requests.post(AGENT_URL, files=files, data=data, timeout=60)
            resp.raise_for_status()
            entry["agent_response"] = resp.json()
        except requests.RequestException as e:
            entry["agent_response"] = {"error": str(e)}
    print(f"Done: {image_path}")

    if i < len(ground_truth) - 1:
        time.sleep(DELAY_SECONDS)

with open("eval_results.json", "w") as f:
    json.dump(ground_truth, f, indent=2)

print("\nAll done. Saved to eval_results.json")