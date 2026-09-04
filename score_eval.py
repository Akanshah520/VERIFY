import json

RESULTS_PATH = "eval_results.json"

with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

scored = []
degraded = []

tp_total = fp_total = fn_total = 0

for entry in results:
    agent_response = entry.get("agent_response", {})
    details = agent_response.get("_details", {})

    if details.get("extraction_error") or "error" in agent_response:
        degraded.append(entry["image"])
        continue

    scored.append(entry["image"])

    ground_truth_cas = {
        hit["cas_number"] for hit in entry.get("verified_carcinogen_hits", [])
    }
    predicted_cas = {
        hit["match"]["cas_number"] for hit in details.get("confirmed_hits", [])
    }

    tp = len(ground_truth_cas & predicted_cas)
    fp = len(predicted_cas - ground_truth_cas)
    fn = len(ground_truth_cas - predicted_cas)

    tp_total += tp
    fp_total += fp
    fn_total += fn

    if fp or fn:
        print(f"{entry['image']}: TP={tp} FP={fp} FN={fn}")
        if fp:
            print(f"  False positive CAS: {predicted_cas - ground_truth_cas}")
        if fn:
            print(f"  False negative CAS: {ground_truth_cas - predicted_cas}")

precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else float("nan")
recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) else float("nan")
f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else float("nan")

print(f"\n--- Scored on {len(scored)} of {len(results)} products (excluding {len(degraded)} degraded) ---")
print(f"TP={tp_total} FP={fp_total} FN={fn_total}")
print(f"Precision: {precision:.3f}")
print(f"Recall:    {recall:.3f}")
print(f"F1:        {f1:.3f}")

if degraded:
    print(f"\n--- Excluded (degraded, extraction_error) ---")
    for img in degraded:
        print(f"  {img}")