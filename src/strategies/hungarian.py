from typing import List
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.models import Match, Participant
from src.strategies.base import MatcherStrategy

class HungarianMatcher(MatcherStrategy):
    """
    Finds the globally optimal assignment maximizing the total compatibility score
    using the Hungarian algorithm (Kuhn-Munkres via scipy linear_sum_assignment).
    
    Mentors are cloned according to their capacity, and the affinity matrix is 
    inverted into a cost matrix using vectorized NumPy operations.
    """
    def match(
        self, 
        mentors: List[Participant], 
        mentees: List[Participant], 
        score_matrix: pd.DataFrame
    ) -> List[Match]:
        if not mentors or not mentees:
            return []

        # 1. Expand mentors based on capacity (Node Cloning)
        expanded_mentors: List[Participant] = []
        for mentor in mentors:
            for _ in range(mentor.capacity):
                expanded_mentors.append(mentor)

        # 2. Extract 2D score array aligned with expanded mentors and mentees
        expanded_mentor_ids = [m.id for m in expanded_mentors]
        mentee_ids = [m.id for m in mentees]

        score_values = score_matrix.loc[expanded_mentor_ids, mentee_ids].to_numpy(dtype=float)

        # 3. Vectorized Cost Matrix: Hungarian minimizes cost, so Cost = (Max_Score + 1.0) - Score
        max_score = float(score_values.max()) + 1.0 if score_values.size > 0 else 1.0
        cost_matrix = max_score - score_values

        # 4. Run linear sum assignment (Hungarian algorithm)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # 5. Reconstruct Matches
        matches: List[Match] = []
        for r, c in zip(row_ind, col_ind):
            mentor = expanded_mentors[r]
            mentee = mentees[c]
            matches.append(Match(mentor=mentor, mentee=mentee, score=float(score_values[r, c])))

        return matches