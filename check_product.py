import sys
import re
import io
import requests
import pdfplumber

from extract_only import extract_ingredients_from_image

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def load_iarc_list():
    IARC_PDF_URL = "https://monographs.iarc.who.int/wp-content/uploads/2018/09/List_of_Classifications.pdf"
    resp = requests.get(IARC_PDF_URL, headers=BROWSER_HEADERS, timeout=30)
    resp.raise_for_status()

    cas_pattern = re.compile(r"^\d{2,7}-\d{2}-\d$")
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
                if not cas or not cas_pattern.match(cas.strip()):
                    continue
                if group not in ("1", "2A", "2B"):
                    continue
                records.append({
                    "cas_number": cas.strip(),
                    "chemical_name": html_tag_pattern.sub("", (agent or "")).strip(),
                    "toxicity_type": f"IARC Group {group}",
                })
    return records

GENERIC_WORDS = {
    "powder", "extract", "acid", "oil", "solution", "compound",
    "mixture", "based", "product", "agent", "substance", "material",
}

def is_real_match(ingredient: str, chemical_name: str) -> bool:
    ing_words = set(re.findall(r"\b\w+\b", ingredient.lower()))
    chem_words = set(re.findall(r"\b\w+\b", chemical_name.lower()))
    significant_words = {w for w in ing_words if len(w) > 3 and w not in GENERIC_WORDS}
    chem_significant = {w for w in chem_words if w not in GENERIC_WORDS}
    return bool(significant_words & chem_significant)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_product.py <path_to_image>")
        sys.exit(1)

    print("Extracting ingredients from image...")
    ingredients = extract_ingredients_from_image(sys.argv[1])

    print("Loading IARC reference list...")
    iarc_records = load_iarc_list()

    print(f"\n{'='*60}")
    print(f"Checked {len(ingredients)} ingredients against {len(iarc_records)} IARC entries")
    print(f"{'='*60}\n")

    for ing in ingredients:
        matches = [r for r in iarc_records if is_real_match(ing, r["chemical_name"])]
        if matches:
            print(f"🚩 FLAGGED: {ing}")
            for m in matches:
                print(f"      -> {m['chemical_name']} ({m['toxicity_type']})")
        else:
            print(f"   clear: {ing}")