import sys
import os
import json
import base64
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

def extract_ingredients_from_image(image_path: str) -> list[str]:
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    response = groq_client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        reasoning_effort="none",
        response_format={"type": "json_object"},
        max_completion_tokens=4096,  # <-- the fix: prevents truncation on long ingredient lists
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
    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    return [i.strip() for i in parsed.get("ingredients", []) if i.strip()]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_only.py <path_to_image>")
        sys.exit(1)

    ingredients = extract_ingredients_from_image(sys.argv[1])
    print(f"\nFound {len(ingredients)} ingredients:\n")
    for i, name in enumerate(ingredients, 1):
        print(f"{i}. {name}")