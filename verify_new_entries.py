import json
from check_product import load_iarc_list, get_cas_number

ingredients = [
    "OCTYLDODECANOL", "RICINUS COMMUNIS (CASTOR) SEED OIL", "SILICA", "TRICAPRYLYL CITRATE",
    "ISONONYL ISONONANOATE", "OZOKERITE", "PARAFFIN", "PHENYL TRIMETHICONE", "MICROCRYSTALLINE WAX",
    "CAPRYLIC/CAPRIC TRIGLYCERIDE", "COPERNICIA CERIFERA (CARNAUBA) WAX", "ASCORBYL PALMITATE",
    "TOCOPHEROL", "STEARYL STEAROYL STEARATE", "VANILLIN", "BHT", "MICA", "TITANIUM DIOXIDE",
    "IRON OXIDES", "BLUE 1 LAKE", "CARMINE", "RED 6 LAKE", "RED 7 LAKE", "RED 21 LAKE",
    "RED 28 LAKE", "RED 30 LAKE", "RED 33 LAKE", "YELLOW 5 LAKE", "YELLOW 6 LAKE",
]

iarc_records = load_iarc_list()
cas_lookup = {r["cas_number"]: r for r in iarc_records}

confirmed = []
for ing in ingredients:
    cas = get_cas_number(ing)
    if cas and cas in cas_lookup:
        confirmed.append({
            "ingredient": ing, "cas_number": cas,
            "matched_name": cas_lookup[cas]["chemical_name"],
            "toxicity_type": cas_lookup[cas]["toxicity_type"],
        })

entry = {
    "image": "image_corpus\\mac_lipstick_pt.jpg",
    "product_type": "topical",
    "extracted_ingredients": ingredients,
    "verified_carcinogen_hits": confirmed,
    "note": "Ingredient list manually transcribed from source image; Groq vision extraction hit output token limit on this product's unusually long ingredient list.",
}

with open("eval_ground_truth.json", "r") as f:
    dataset = json.load(f)
dataset.append(entry)
with open("eval_ground_truth.json", "w") as f:
    json.dump(dataset, f, indent=2)

print(f"Added. Dataset now has {len(dataset)} products.")
print(f"Verified hits: {len(confirmed)}")