import os
import json
from dotenv import load_dotenv
from groq import Groq, BadRequestError
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from .state import AgentState

load_dotenv()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
kb_index = pc.Index("ingredient-carcinogens")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def _call_extraction(image_b64: str, max_tokens: int):
    return groq_client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        reasoning_effort="none",
        response_format={"type": "json_object"},
        max_completion_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Read the ingredients list on this product label. "
                    "Respond with ONLY a JSON object of this exact shape, no other text: "
                    '{"ingredients": ["ingredient one", "ingredient two", ...]}. '
                    "Split compound/bracketed ingredients into their individual components."
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ],
        }],
        temperature=0,
    )


def extract_ingredients(state: AgentState) -> AgentState:
    try:
        response = _call_extraction(state["image_b64"], max_tokens=2048)
    except BadRequestError as e:
        if getattr(e, "code", None) == "json_validate_failed" or "json_validate_failed" in str(e):
            print("--- extraction hit token cap before valid JSON, retrying with higher cap ---")
            try:
                response = _call_extraction(state["image_b64"], max_tokens=4096)
            except BadRequestError as e2:
                if getattr(e2, "code", None) == "json_validate_failed" or "json_validate_failed" in str(e2):
                    print("--- retry also hit token cap; returning partial failure instead of crashing ---")
                    return {
                        **state,
                        "raw_ingredients": [],
                        "extraction_error": "Ingredient list too long/complex to extract reliably; manual review recommended.",
                    }
                raise
        else:
            raise

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
    names = [item["resolved_name"] for item in state["normalized_ingredients"]]
    if not names:
        return {**state, "confirmed_hits": [], "unmatched": []}

    vectors = embed_model.encode(names, normalize_embeddings=True)

    confirmed, unmatched = [], []
    for name, vec in zip(names, vectors):
        result = kb_index.query(vector=vec.tolist(), top_k=3, include_metadata=True)

        print(f"\n=== INGREDIENT: {name} ===")
        for m in result["matches"]:
            print(
                "score =", m["score"],
                "| metadata =", m["metadata"]
            )

        match = result["matches"][0] if result["matches"] else None

        if match and match["score"] >= 0.80:
            confirmed.append({
                "ingredient": name,
                "match": match["metadata"],
                "score": match["score"]
            })
        else:
            unmatched.append(name)

    return {**state, "confirmed_hits": confirmed, "unmatched": unmatched}

def reason_unmatched(state: AgentState) -> AgentState:
    reasoned = [
        {"ingredient": name, "flag": "not yet checked", "confidence_tier": "unknown"}
        for name in state["unmatched"]
    ]
    return {**state, "reasoned_hits": reasoned}


def confidence_label(score: float) -> str:
    """Tiers informed directly by eval results: a correct coal-tar match scored
    0.800, a false positive (hydrochloric acid) scored 0.825 -- anything in that
    narrow band gets an explicit caveat rather than false confidence."""
    if score >= 0.95:
        return "High confidence"
    elif score >= 0.85:
        return "Moderate confidence"
    else:
        return "Low confidence - borderline match, verify manually"


def synthesize_report(state: AgentState) -> AgentState:
    if state.get("extraction_error"):
        report = {
            "summary": f"⚠️ Unable to reliably extract ingredients: {state['extraction_error']}",
            "flagged_ingredients": [],
            "ingredients_not_evaluated": None,
            "_details": {
                "confirmed_hits": [],
                "reasoned_hits": [],
                "extraction_error": state["extraction_error"],
            },
        }
        return {**state, "report": report}

    flagged = []
    for hit in state["confirmed_hits"]:
        match = hit["match"]
        flagged.append({
            "ingredient": hit["ingredient"],
            "classification": match.get("toxicity_type", "Unknown"),
            "source": match.get("source", "IARC"),
            "confidence_score": round(min(hit["score"], 1.0), 3),
            "confidence_label": confidence_label(hit["score"]),
        })

    if flagged:
        summary = f"⚠️ {len(flagged)} ingredient(s) flagged as known/possible carcinogens."
    else:
        summary = "✅ No known carcinogens identified in this product's ingredient list."

    report = {
        "summary": summary,
        "flagged_ingredients": flagged,
        "ingredients_not_evaluated": len(state["unmatched"]),
        "_details": {
            "confirmed_hits": state["confirmed_hits"],
            "reasoned_hits": state["reasoned_hits"],
        },
    }
    return {**state, "report": report}