from check_product import load_iarc_list, get_cas_number

test_ingredients = ["Formaldehyde", 
    "Aflatoxin",
    "Benzo[a]pyrene",]

iarc_records = load_iarc_list()
cas_lookup = {r["cas_number"]: r for r in iarc_records}

for ing in test_ingredients:
    cas = get_cas_number(ing)
    if cas is None:
        print(f"n/a: {ing}")
        continue
    match = cas_lookup.get(cas)
    if match:
        print(f"🚩 FLAGGED: {ing} -> {match['chemical_name']} ({match['toxicity_type']})")
    else:
        print(f"clear: {ing} (CAS {cas})")