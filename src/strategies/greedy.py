from typing import List
import pandas as pd
from src.strategies.base import MatcherStrategy
from src.models import Participant, Match

class GreedyMatcher(MatcherStrategy):
    def match(self, mentors, mentees, score_matrix) -> List[Match]:
        matches = []
        # Track available capacity for mentors
        mentor_remaining_cap = {m.id: m.capacity for m in mentors}
        mentee_assigned = set()

        # 1. Convert matrix to a list of potential edges: (score, mentor_id, mentee_id)
        edges = []
        for mentor in mentors:
            for mentee in mentees:
                score = score_matrix.loc[mentor.id, mentee.id]
                edges.append((score, mentor, mentee))

        # 2. Sort by score descending (Highest first)
        edges.sort(key=lambda x: x[0], reverse=True)

        # 3. Iterate and assign
        for score, mentor, mentee in edges:
            if mentee.id in mentee_assigned:
                continue
            
            if mentor_remaining_cap[mentor.id] > 0:
                # Make the match
                matches.append(Match(mentor=mentor, mentee=mentee, score=score))
                mentor_remaining_cap[mentor.id] -= 1
                mentee_assigned.add(mentee.id)

        return matches