import sys
import re
import io
import time
import urllib.parse
import requests
import pdfplumber

from extract_only import extract_ingredients_from_image

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")

# Manually verified entries missing from the source PDF (added since Volume 123,
# or listed under a name PubChem can't resolve automatically) -- keeps this
# checker in sync with what's actually in the live Pinecone knowledge base.
MANUAL_ADDITIONS = [
    {"cas_number": "22839-47-0", "chemical_name": "Aspartame", "toxicity_type": "IARC Group 2B"},
    {"cas_number": "93-15-2", "chemical_name": "Methyleugenol", "toxicity_type": "IARC Group 2A"},
    {"cas_number": "97-54-1", "chemical_name": "Isoeugenol", "toxicity_type": "IARC Group 2B"},
]

# Names PubChem can't resolve to a CAS number automatically, where the correct
# number has been independently confirmed via search_kb_source.py.
MANUAL_CAS_OVERRIDES = {
    "coal tar": "8007-45-2",
    "coal tar extract": "8007-45-2",
    "solubilized coal tar extract": "8007-45-2",
    "sulfolated coal tar extract": "8007-45-2",
}


def load_iarc_list():
    IARC_PDF_URL = "https://monographs.iarc.who.int/wp-content/uploads/2018/09/List_of_Classifications.pdf"
    resp = requests.get(IARC_PDF_URL, headers=BROWSER_HEADERS, timeout=30)
    resp.raise_for_status()

    html_tag_pattern = re.compile(r"<[^>]+>")
    records = []

    with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if not row or len(row) < 3:
                    continue
                cas, agent, group = row[0], row[1], row[2]
                if not cas or not CAS_PATTERN.match(cas.strip()):
                    continue
                if group not in ("1", "2A", "2B"):
                    continue
                records.append({
                    "cas_number": cas.strip(),
                    "chemical_name": html_tag_pattern.sub("", (agent or "")).strip(),
                    "toxicity_type": f"IARC Group {group}",
                })

    records.extend(MANUAL_ADDITIONS)  # <-- fix #2, applied here
    return records


def get_cas_number(ingredient_name: str) -> str | None:
    override = MANUAL_CAS_OVERRIDES.get(ingredient_name.strip().lower())  # <-- fix #1, applied here
    if override:
        return override

    encoded = urllib.parse.quote(ingredient_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/synonyms/JSON"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        synonyms = resp.json()["InformationList"]["Information"][0]["Synonym"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None
    for syn in synonyms:
        if CAS_PATTERN.match(syn.strip()):
            return syn.strip()
    return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_product.py <path_to_image>")
        sys.exit(1)

    print("Extracting ingredients from image...")
    ingredients = extract_ingredients_from_image(sys.argv[1])

    print("Loading IARC reference list...")
    iarc_records = load_iarc_list()
    cas_lookup = {r["cas_number"]: r for r in iarc_records}

    print(f"\n{'='*60}")
    print(f"Checking {len(ingredients)} ingredients via CAS number cross-reference")
    print(f"{'='*60}\n")

    for ing in ingredients:
        cas = get_cas_number(ing)
        time.sleep(0.3)
        if cas is None:
            print(f"   n/a (not a single compound): {ing}")
            continue
        match = cas_lookup.get(cas)
        if match:
            print(f"🚩 FLAGGED: {ing}")
            print(f"      -> {match['chemical_name']} ({match['toxicity_type']})")
        else:
            print(f"   clear: {ing}  (CAS {cas} exists, not on IARC list)")