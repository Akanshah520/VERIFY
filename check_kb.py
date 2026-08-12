import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("ingredient-carcinogens")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Index stats:", index.describe_index_stats())

query = "Formaldehyde"
vec = model.encode([query], normalize_embeddings=True)[0].tolist()
result = index.query(vector=vec, top_k=3, include_metadata=True)

print(f"\nQuery: '{query}'")
for match in result["matches"]:
    print(f"  score={match['score']:.3f}  {match['metadata']}")