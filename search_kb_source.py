import re
import io
import requests
import pdfplumber

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

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

print(f"Loaded {len(records)} entries.\n")

while True:
    term = input("Search term (or 'quit'): ").strip()
    if term.lower() == "quit":
        break
    matches = [r for r in records if term.lower() in r["chemical_name"].lower()]
    if matches:
        for m in matches:
            print(f"  ✓ {m['chemical_name']}  ({m['toxicity_type']}, CAS {m['cas_number']})")
    else:
        print(f"  ✗ No match for '{term}'")
    print()