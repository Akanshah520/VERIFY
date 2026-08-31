import os
from build_eval_set import build_ground_truth_entry, DATASET_PATH
import json

IMAGE_DIR = "image_corpus"

def guess_product_type(filename: str) -> str:
    return "edible" if "_pe" in filename or "_ne" in filename else "topical"

dataset = []
for filename in sorted(os.listdir(IMAGE_DIR)):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".jfif")):
        continue
    path = os.path.join(IMAGE_DIR, filename)
    product_type = guess_product_type(filename)
    print(f"Processing {filename} ({product_type})...")
    try:
        entry = build_ground_truth_entry(path, product_type)
        dataset.append(entry)
    except Exception as e:
        print(f"  FAILED: {filename} -> {e}")

with open(DATASET_PATH, "w") as f:
    json.dump(dataset, f, indent=2)

print(f"\nDone. {len(dataset)} products processed into {DATASET_PATH}.")