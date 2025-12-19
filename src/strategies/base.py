from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from src.models import Participant, Match

class MatcherStrategy(ABC):
    """
    The Contract: Any algorithm must implement this method.
    """
    @abstractmethod
    def match(
        self, 
        mentors: List[Participant], 
        mentees: List[Participant],
        score_matrix: pd.DataFrame
    ) -> List[Match]:
        pass