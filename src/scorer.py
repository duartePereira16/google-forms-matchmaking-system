from typing import Any, Dict
from src.models import Participant

def compute_match_score(
    p1: Participant, 
    p2: Participant, 
    scoring_configs: Dict[str, Any]
) -> float:
    """
    Calculates the compatibility score between two participants based on weighted question logic.
    """
    score = 0.0
    weights: Dict[str, float] = scoring_configs.get("weights", {})
    default_cb_weight: float = scoring_configs.get("default_checkbox_weight", 1.0)
    default_mc_weight: float = scoring_configs.get("default_multiple_choice_weight", 1.0)

    # ---- Checkbox questions ----
    common_cb_questions = p1.check_box_answers.keys() & p2.check_box_answers.keys()
    for question in common_cb_questions:
        intersection_nr = len(p1.check_box_answers[question] & p2.check_box_answers[question])
        if intersection_nr > 0:
            weight = weights.get(question, default_cb_weight)
            score += intersection_nr * weight

    # ---- Multiple choice questions ----
    common_mc_questions = p1.multiple_choice_answers.keys() & p2.multiple_choice_answers.keys()
    for question in common_mc_questions:
        if p1.multiple_choice_answers[question] == p2.multiple_choice_answers[question]:
            weight = weights.get(question, default_mc_weight)
            score += weight

    return score