import numpy as np
import pandas as pd
import pytest

from src.models import Match, Participant
from src.strategies.greedy import GreedyMatcher
from src.strategies.hungarian import HungarianMatcher
from src.strategies.iterative_greedy import IterativeGreedyMatcher

@pytest.fixture
def sample_participants():
    m1 = Participant("m1", "Mentor One", {}, {}, {}, capacity=1)
    m2 = Participant("m2", "Mentor Two", {}, {}, {}, capacity=2)
    e1 = Participant("e1", "Mentee One", {}, {}, {})
    e2 = Participant("e2", "Mentee Two", {}, {}, {})
    e3 = Participant("e3", "Mentee Three", {}, {}, {})
    return [m1, m2], [e1, e2, e3]

def test_hungarian_matcher_optimal_assignment(sample_participants):
    """Verify Hungarian assigns matches maximizing global score respecting capacities."""
    mentors, mentees = sample_participants
    # m2 has capacity 2, m1 has capacity 1.
    # Scores:
    #      e1   e2   e3
    # m1  10.0  1.0  1.0
    # m2   2.0  9.0  8.0
    # Optimal: (m1, e1) [10], (m2, e2) [9], (m2, e3) [8] -> Total: 27
    score_df = pd.DataFrame(
        [
            [10.0, 1.0, 1.0],
            [2.0, 9.0, 8.0]
        ],
        index=["m1", "m2"],
        columns=["e1", "e2", "e3"]
    )

    matcher = HungarianMatcher()
    matches = matcher.match(mentors, mentees, score_df)

    assert len(matches) == 3
    total_score = sum(m.score for m in matches)
    assert total_score == pytest.approx(27.0)

    # Check mentor capacity constraints
    m1_matches = [m for m in matches if m.mentor.id == "m1"]
    m2_matches = [m for m in matches if m.mentor.id == "m2"]
    assert len(m1_matches) == 1
    assert len(m2_matches) == 2
    assert m1_matches[0].mentee.id == "e1"

def test_greedy_matcher_assignment(sample_participants):
    """Verify GreedyMatcher assigns highest global edge first."""
    mentors, mentees = sample_participants
    score_df = pd.DataFrame(
        [
            [10.0, 5.0, 1.0],
            [2.0, 9.0, 8.0]
        ],
        index=["m1", "m2"],
        columns=["e1", "e2", "e3"]
    )

    matcher = GreedyMatcher()
    matches = matcher.match(mentors, mentees, score_df)

    assert len(matches) == 3
    # Highest edge is (m1, e1, 10.0), next is (m2, e2, 9.0), next is (m2, e3, 8.0)
    match_pairs = {(m.mentor.id, m.mentee.id) for m in matches}
    assert match_pairs == {("m1", "e1"), ("m2", "e2"), ("m2", "e3")}

def test_iterative_greedy_matcher_assignment(sample_participants):
    """Verify IterativeGreedyMatcher evaluates mentees sequentially in column order."""
    mentors, mentees = sample_participants
    score_df = pd.DataFrame(
        [
            [10.0, 10.0, 1.0],
            [2.0, 9.0, 8.0]
        ],
        index=["m1", "m2"],
        columns=["e1", "e2", "e3"]
    )

    matcher = IterativeGreedyMatcher()
    matches = matcher.match(mentors, mentees, score_df)

    assert len(matches) == 3
    # e1 takes m1 (capacity m1 -> 0)
    # e2 wants m1, but m1 is full, so takes m2
    # e3 takes m2
    match_dict = {m.mentee.id: m.mentor.id for m in matches}
    assert match_dict["e1"] == "m1"
    assert match_dict["e2"] == "m2"
    assert match_dict["e3"] == "m2"

def test_matchers_handle_empty_input():
    """Verify all matchers return an empty list when participants are empty."""
    score_df = pd.DataFrame()
    for MatcherClass in [HungarianMatcher, GreedyMatcher, IterativeGreedyMatcher]:
        matcher = MatcherClass()
        assert matcher.match([], [], score_df) == []

