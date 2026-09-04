import json

import requests

RESULTS_PATH = "eval_results.json"
AGENT_URL = "https://ingredient-agent-247055277121.us-central1.run.app/analyze"
TARGET_IMAGE = "image_corpus\\coke_pe.jfif"  # change this to re-run a different single product


with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

entry = next((e for e in results if e["image"] == TARGET_IMAGE), None)

if entry is None:
    raise SystemExit(f"No entry found for {TARGET_IMAGE} in {RESULTS_PATH}")

image_path = entry["image"]
with open(image_path, "rb") as f:
    files = {"image": f}
    data = {"product_type": entry["product_type"]}
    resp = requests.post(AGENT_URL, files=files, data=data, timeout=60)
    resp.raise_for_status()
    new_response = resp.json()

entry["agent_response"] = new_response

still_degraded = bool(new_response.get("_details", {}).get("extraction_error"))
confirmed = new_response.get("_details", {}).get("confirmed_hits", [])
matched_cas = {hit["match"]["cas_number"] for hit in confirmed}

print(f"{image_path}: {'still degraded' if still_degraded else 'clean response'}")
print(f"Confirmed CAS numbers this run: {matched_cas or 'none'}")

with open(RESULTS_PATH, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nUpdated {RESULTS_PATH} for {image_path}.")