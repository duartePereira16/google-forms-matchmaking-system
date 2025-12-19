from typing import List
import pandas as pd
from src.strategies.base import MatcherStrategy
from src.models import Participant, Match

class IterativeGreedyMatcher(MatcherStrategy):
    def match(self, mentors, mentees, score_matrix) -> List[Match]:
        matches = []
        mentor_remaining_cap = {m.id: m.capacity for m in mentors}

        # Iterate through mentees in order (Rows of the DF)
        for mentee_id in score_matrix.columns:
            mentee = next(m for m in mentees if m.id == mentee_id)
            
            # Get all scores for this specific mentee
            # This is equivalent to your inner loop over veterans
            candidates = score_matrix[mentee_id].sort_values(ascending=False)
            
            best_match_mentor = None
            best_score = -1

            # Find best available mentor
            for mentor_id, score in candidates.items():
                if mentor_remaining_cap[mentor_id] > 0:
                    best_match_mentor = next(m for m in mentors if m.id == mentor_id)
                    best_score = score
                    break # Found the highest score available!

            if best_match_mentor:
                matches.append(Match(best_match_mentor, mentee, best_score))
                mentor_remaining_cap[best_match_mentor.id] -= 1

        return matches