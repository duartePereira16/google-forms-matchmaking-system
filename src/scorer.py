from src.models import Participant

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Returns intersection over union (0.0 to 1.0)."""
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def compute_match_score(
    p1: Participant, 
    p2: Participant, 
    weights: dict
) -> float:
    """
    Calculates compatibility score based on weighted logic.
    """
    score = 0.0
    
    # 1. Checkbox Questions (Set Intersection)
    # We assume 'interests' is pre-processed into a set
    common_interests = len(p1.interests & p2.interests)
    score += common_interests * weights.get("checkbox_weight", 1.0)
    
    # 2. Multiple Choice (Exact Match)
    # Iterate through keys that exist in both
    common_keys = set(p1.attributes.keys()) & set(p2.attributes.keys())
    for key in common_keys:
        if p1.attributes[key] == p2.attributes[key]:
             score += weights.get("multiple_choice_weight", 2.0)
             
    return score