import base64
import json
from app.agent.graph import agent

with open("sample_label.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

initial_state = {
    "image_b64": image_b64,
    "product_type": "edible",   # or "topical", depending on your photo
    "raw_ingredients": [],
    "normalized_ingredients": [],
    "confirmed_hits": [],
    "unmatched": [],
    "reasoned_hits": [],
    "report": None,
}

result = agent.invoke(initial_state)
print(json.dumps(result["report"], indent=2))