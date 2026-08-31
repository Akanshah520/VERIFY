import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("ingredient-carcinogens")
model = SentenceTransformer("all-MiniLM-L6-v2")

new_entries = [
    {"cas_number": "22839-47-0", "chemical_name": "Aspartame", "toxicity_type": "IARC Group 2B", "jurisdiction": "global", "source": "IARC (Vol. 134, 2023 - manually verified)"},
    {"cas_number": "93-15-2", "chemical_name": "Methyleugenol", "toxicity_type": "IARC Group 2A", "jurisdiction": "global", "source": "IARC (Vol. 134, 2023 - manually verified)"},
    {"cas_number": "97-54-1", "chemical_name": "Isoeugenol", "toxicity_type": "IARC Group 2B", "jurisdiction": "global", "source": "IARC (Vol. 134, 2023 - manually verified)"},
]

names = [e["chemical_name"] for e in new_entries]
embeddings = model.encode(names, normalize_embeddings=True)

vectors = [
    {
        "id": f"iarc-vol134-{i}",
        "values": embeddings[i].tolist(),
        "metadata": new_entries[i],
    }
    for i in range(len(new_entries))
]

index.upsert(vectors=vectors)
print(f"Added {len(vectors)} entries.")
print("New index stats:", index.describe_index_stats())