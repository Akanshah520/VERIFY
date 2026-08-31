import sys
import json
import os

from check_product import load_iarc_list, get_cas_number
from extract_only import extract_ingredients_from_image

DATASET_PATH = "eval_ground_truth.json"


def build_ground_truth_entry(image_path: str, product_type: str) -> dict:
    ingredients = extract_ingredients_from_image(image_path)
    iarc_records = load_iarc_list()
    cas_lookup = {r["cas_number"]: r for r in iarc_records}

    confirmed = []
    for ing in ingredients:
        cas = get_cas_number(ing)
        if cas and cas in cas_lookup:
            confirmed.append({
                "ingredient": ing,
                "cas_number": cas,
                "matched_name": cas_lookup[cas]["chemical_name"],
                "toxicity_type": cas_lookup[cas]["toxicity_type"],
            })

    return {
        "image": image_path,
        "product_type": product_type,
        "extracted_ingredients": ingredients,
        "verified_carcinogen_hits": confirmed,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_eval_set.py <image_path> <edible|topical>")
        sys.exit(1)

    entry = build_ground_truth_entry(sys.argv[1], sys.argv[2])

    dataset = []
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, "r") as f:
            dataset = json.load(f)

    dataset.append(entry)
    with open(DATASET_PATH, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Added entry for {sys.argv[1]}. Dataset now has {len(dataset)} product(s).")
    print(f"Verified hits: {len(entry['verified_carcinogen_hits'])}")