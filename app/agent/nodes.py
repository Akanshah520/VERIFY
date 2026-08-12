import os
import json
from dotenv import load_dotenv
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from .state import AgentState

load_dotenv()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
kb_index = pc.Index("ingredient-carcinogens")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_ingredients(state: AgentState) -> AgentState:
    response = groq_client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Read the ingredients list on this product label. "
                    "Respond with ONLY a JSON object of this exact shape, no other text: "
                    '{"ingredients": ["ingredient one", "ingredient two", ...]}. '
                    "Split compound/bracketed ingredients into their individual components."
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_b64']}"}},
            ],
        }],
        temperature=0,
    )
    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        ingredients = [i.strip() for i in parsed.get("ingredients", []) if i.strip()]
    except json.JSONDecodeError:
        print("--- Model did not return valid JSON, raw output below ---")
        print(raw)
        raise
    return {**state, "raw_ingredients": ingredients}


INS_DECODER = {}  # filled in later, once the KB knowledge-base step is built

def normalize_ingredients(state: AgentState) -> AgentState:
    normalized = []
    for ing in state["raw_ingredients"]:
        code_key = ing.upper().replace("INS ", "E").replace("INS", "E").strip()
        decoded = INS_DECODER.get(code_key) if state["product_type"] == "edible" else None
        normalized.append({"raw": ing, "resolved_name": decoded or ing})
    return {**state, "normalized_ingredients": normalized}


def kb_lookup(state: AgentState) -> AgentState:
    confirmed, unmatched = [], []
    for item in state["normalized_ingredients"]:
        vec = embed_model.encode([item["resolved_name"]], normalize_embeddings=True)[0].tolist()
        result = kb_index.query(vector=vec, top_k=1, include_metadata=True)
        match = result["matches"][0] if result["matches"] else None
        if match and match["score"] >= 0.80:
            confirmed.append({"ingredient": item["resolved_name"], "match": match["metadata"], "score": match["score"]})
        else:
            unmatched.append(item["resolved_name"])
    return {**state, "confirmed_hits": confirmed, "unmatched": unmatched}


def reason_unmatched(state: AgentState) -> AgentState:
    reasoned = [
        {"ingredient": name, "flag": "not yet checked", "confidence_tier": "unknown"}
        for name in state["unmatched"]
    ]
    return {**state, "reasoned_hits": reasoned}


def synthesize_report(state: AgentState) -> AgentState:
    report = {
        "confirmed": state["confirmed_hits"],
        "reasoned": state["reasoned_hits"],
        "summary": f"{len(state['confirmed_hits'])} confirmed hit(s), "
                   f"{len(state['unmatched'])} ingredient(s) not yet checked.",
    }
    return {**state, "report": report}