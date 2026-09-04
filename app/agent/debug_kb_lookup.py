from app.agent.nodes import embed_model, kb_index

names_to_check = ["Talc", "Aspartame", "Alcohol"]

vectors = embed_model.encode(names_to_check, normalize_embeddings=True)

for name, vec in zip(names_to_check, vectors):
    result = kb_index.query(vector=vec.tolist(), top_k=3, include_metadata=True)
    print(f"\n=== {name} ===")
    for m in result["matches"]:
        print(f"  score={m['score']:.4f}  cas={m['metadata'].get('cas_number')}  name={m['metadata'].get('chemical_name')}")