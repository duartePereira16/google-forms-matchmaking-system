from typing import Dict, List
import pandas as pd
from src.models import Match, Participant
from src.strategies.base import MatcherStrategy

class IterativeGreedyMatcher(MatcherStrategy):
    """
    Greedy assignment iterating sequentially over each mentee, picking their highest-scoring
    available mentor. Lookups are pre-indexed into dictionaries for O(1) retrieval.
    """
    def match(
        self, 
        mentors: List[Participant], 
        mentees: List[Participant], 
        score_matrix: pd.DataFrame
    ) -> List[Match]:
        matches: List[Match] = []
        mentor_remaining_cap: Dict[str, int] = {m.id: m.capacity for m in mentors}
        mentors_by_id: Dict[str, Participant] = {m.id: m for m in mentors}
        mentees_by_id: Dict[str, Participant] = {m.id: m for m in mentees}

        for mentee_id in score_matrix.columns:
            mentee = mentees_by_id.get(mentee_id)
            if not mentee:
                continue
            
            # Sort mentor candidates descending by score for this mentee
            candidates = score_matrix[mentee_id].sort_values(ascending=False)
            
            best_match_mentor = None
            best_score = -1.0

            for mentor_id, score in candidates.items():
                if mentor_remaining_cap.get(mentor_id, 0) > 0:
                    best_match_mentor = mentors_by_id.get(mentor_id)
                    best_score = float(score)
                    break

            if best_match_mentor:
                matches.append(Match(mentor=best_match_mentor, mentee=mentee, score=best_score))
                mentor_remaining_cap[best_match_mentor.id] -= 1

        return matches