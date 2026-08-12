from app.agent.nodes import kb_lookup

test_state = {
    "normalized_ingredients": [
        {"raw": "Formaldehyde", "resolved_name": "Formaldehyde"},
        {"raw": "formaldehyd", "resolved_name": "formaldehyd"},  # deliberate typo — tests fuzzy matching
    ],
}

result = kb_lookup(test_state)
print("Confirmed:", result["confirmed_hits"])
print("Unmatched:", result["unmatched"])