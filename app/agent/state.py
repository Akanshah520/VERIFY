from typing import TypedDict, List, Dict, Optional

class AgentState(TypedDict):
    image_b64: str
    product_type: str

    raw_ingredients: List[str]
    normalized_ingredients: List[Dict]
    confirmed_hits: List[Dict]
    unmatched: List[str]
    reasoned_hits: List[Dict]
    report: Optional[Dict]