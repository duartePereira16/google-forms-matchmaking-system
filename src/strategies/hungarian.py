from typing import List
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from src.strategies.base import MatcherStrategy
from src.models import Participant, Match

class HungarianMatcher(MatcherStrategy):
    def match(self, mentors, mentees, score_matrix) -> List[Match]:
        
        # 1. Expand Mentors based on capacity (Node Cloning)
        # If Mentor A has capacity 2, we create Mentor A_1, Mentor A_2
        expanded_mentors = []
        for mentor in mentors:
            for _ in range(mentor.capacity):
                expanded_mentors.append(mentor)
        
        # 2. Build the Cost Matrix
        # Hungarian minimizes cost, so Cost = (Max_Possible_Score - Actual_Score)
        # We need a matrix of size (N_expanded_mentors x N_mentees)
        max_score = score_matrix.max().max() + 1.0
        
        cost_matrix = np.zeros((len(expanded_mentors), len(mentees)))
        
        for r, mentor in enumerate(expanded_mentors):
            for c, mentee in enumerate(mentees):
                score = score_matrix.loc[mentor.id, mentee.id]
                cost_matrix[r, c] = max_score - score

        # 3. Run Hungarian Algorithm (Scipy)
        # returns row_indices (mentors) and col_indices (mentees)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 4. Reconstruct Matches
        matches = []
        for r, c in zip(row_ind, col_ind):
            mentor = expanded_mentors[r]
            mentee = mentees[c]
            # Retrieve original score
            original_score = score_matrix.loc[mentor.id, mentee.id]
            matches.append(Match(mentor, mentee, original_score))
            
        return matches