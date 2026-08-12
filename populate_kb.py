import re
import io
import requests
import pdfplumber
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

IARC_PDF_URL = "https://monographs.iarc.who.int/wp-content/uploads/2018/09/List_of_Classifications.pdf"

resp = requests.get(IARC_PDF_URL, headers=BROWSER_HEADERS, timeout=30)
resp.raise_for_status()

head = resp.content[:300].lower()
if b"<html" in head or b"<!doctype html" in head:
    raise RuntimeError("Got an HTML page instead of a PDF — this source may be blocking us.")

print(f"Downloaded {len(resp.content)} bytes.")

cas_pattern = re.compile(r"^\d{2,7}-\d{2}-\d$")
html_tag_pattern = re.compile(r"<[^>]+>")
records = []

with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
    print(f"Pages: {len(pdf.pages)}")
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
            clean_name = html_tag_pattern.sub("", (agent or "")).strip()
            records.append({
                "cas_number": cas.strip(),
                "chemical_name": clean_name,
                "toxicity_type": f"IARC Group {group}",
                "jurisdiction": "global",
                "source": "IARC",
            })

print(f"\nParsed {len(records)} Group 1 / 2A / 2B entries.")

# ---------- Embed + upload ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("ingredient-carcinogens")

names = [r["chemical_name"] for r in records]
embeddings = model.encode(names, batch_size=64, show_progress_bar=True, normalize_embeddings=True)

vectors = [
    {
        "id": f"iarc-{i}",
        "values": embeddings[i].tolist(),
        "metadata": records[i],
    }
    for i in range(len(records))
]

BATCH_SIZE = 100
for i in range(0, len(vectors), BATCH_SIZE):
    batch = vectors[i:i + BATCH_SIZE]
    index.upsert(vectors=batch)
    print(f"Upserted {i + len(batch)}/{len(vectors)}")

print("\nDone. Index stats:", index.describe_index_stats())