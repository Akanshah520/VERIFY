import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

INDEX_NAME = "ingredient-carcinogens"

if INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,          # must match the embedding model in nodes.py
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    print("Index created.")
else:
    print("Index already exists.")