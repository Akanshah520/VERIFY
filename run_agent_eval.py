import json
import requests

DATASET_PATH = "eval_ground_truth.json"
AGENT_URL = "https://ingredient-agent-247055277121.us-central1.run.app/analyze"

with open(DATASET_PATH, "r") as f:
    ground_truth = json.load(f)

for entry in ground_truth:
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

with open("eval_results.json", "w") as f:
    json.dump(ground_truth, f, indent=2)

print("\nAll done. Saved to eval_results.json")