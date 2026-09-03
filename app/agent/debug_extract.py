import base64
import traceback

from .nodes import extract_ingredients

IMAGE_PATH = "image_corpus/mac_lipstick_pt.jpg"  # adjust if your repo root differs

with open(IMAGE_PATH, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

state = {"image_b64": image_b64}

try:
    result = extract_ingredients(state)
    print("SUCCESS")
    print(result["raw_ingredients"])
except Exception:
    print("FAILED — full traceback below:")
    traceback.print_exc()