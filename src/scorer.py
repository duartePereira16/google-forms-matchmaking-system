from src.models import Participant

def compute_match_score(
    p1: Participant, 
    p2: Participant, 
    scoring_configs: dict
) -> float:
    """
    Calculates compatibility score based on weighted logic.
    """
    score = 0.0

    question_specific_weights = scoring_configs.get("weights", {})

    def get_question_weight(question, default):
        return question_specific_weights.get(question, scoring_configs.get(default, 1.0))
    
    # ---- check box questions ----
    common_cb_questions = set(p1.check_box_answers.keys()) & set(p2.check_box_answers.keys())       # making sure to only get questions they both answered (for safety) 
    
    for question in common_cb_questions:
        ans_p1 = p1.check_box_answers[question]
        ans_p2 = p2.check_box_answers[question]

        intersection_nr = len(set(ans_p1) & set(ans_p2))

        if intersection_nr > 0:
            weight = get_question_weight(question, 'default_checkbox_weight')
            score += intersection_nr * weight
    
    # ---- multiple choice questions ----
    common_mc_questions = set(p1.multiple_choice_answers.keys()) & set(p2.multiple_choice_answers.keys())       # making sure to only get questions they both answered (for safety)

    for question in common_mc_questions:
        ans_p1 = p1.multiple_choice_answers[question]
        ans_p2 = p2.multiple_choice_answers[question]

        if ans_p1 == ans_p2:
            weight = get_question_weight(question, 'default_multiple_choice_weight')
            score += weight
             
    return score