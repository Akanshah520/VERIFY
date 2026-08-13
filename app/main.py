import base64
from fastapi import FastAPI, UploadFile, File, Form
from app.agent.graph import agent

app = FastAPI(title="Ingredient Safety Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...), product_type: str = Form("edible")):
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    initial_state = {
        "image_b64": image_b64,
        "product_type": product_type,
        "raw_ingredients": [],
        "normalized_ingredients": [],
        "confirmed_hits": [],
        "unmatched": [],
        "reasoned_hits": [],
        "report": None,
    }

    result = agent.invoke(initial_state)
    return result["report"]