from typing import Dict, List, Set, Tuple
import pandas as pd

from src.models import Match, Participant
from src.strategies.base import MatcherStrategy

class GreedyMatcher(MatcherStrategy):
    """
    Global greedy matcher: flattens the affinity matrix into sorted edges and
    iteratively assigns the highest-scoring available mentor-mentee pair.
    """
    def match(
        self, 
        mentors: List[Participant], 
        mentees: List[Participant], 
        score_matrix: pd.DataFrame
    ) -> List[Match]:
        if not mentors or not mentees:
            return []

        matches: List[Match] = []
        mentor_remaining_cap: Dict[str, int] = {m.id: m.capacity for m in mentors}
        mentee_assigned: Set[str] = set()

        # 1. Extract 2D score array aligned with mentors and mentees
        mentor_ids = [m.id for m in mentors]
        mentee_ids = [m.id for m in mentees]
        score_values = score_matrix.loc[mentor_ids, mentee_ids].to_numpy(dtype=float)

        # 2. Build edges: (score, mentor, mentee)
        edges: List[Tuple[float, Participant, Participant]] = []
        for r, mentor in enumerate(mentors):
            for c, mentee in enumerate(mentees):
                edges.append((float(score_values[r, c]), mentor, mentee))

        # 3. Sort by score descending
        edges.sort(key=lambda x: x[0], reverse=True)

        # 4. Iterate and assign
        for score, mentor, mentee in edges:
            if mentee.id in mentee_assigned:
                continue
            
            if mentor_remaining_cap.get(mentor.id, 0) > 0:
                matches.append(Match(mentor=mentor, mentee=mentee, score=score))
                mentor_remaining_cap[mentor.id] -= 1
                mentee_assigned.add(mentee.id)

        return matches