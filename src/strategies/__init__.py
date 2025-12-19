from .greedy import GreedyMatcher
from .iterative_greedy import IterativeGreedyMatcher
from .hungarian import HungarianMatcher

# Create a dictionary map for easy lookup in main.py
ALGORITHMS = {
    "greedy": GreedyMatcher,
    "iterative_greedy": IterativeGreedyMatcher,
    "hungarian": HungarianMatcher
}