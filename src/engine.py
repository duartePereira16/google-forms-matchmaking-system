from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from src.loader import load_participants
from src.scorer import compute_match_score
from src.models import Match, Participant
from src.strategies import ALGORITHMS

@dataclass
class MatchmakingConfig:
    """Configuration parameters defining participant columns, question types, and scoring weights."""
    id_column: str
    name_column: str
    contact_info: List[str] = field(default_factory=list)
    checkbox_questions: List[str] = field(default_factory=list)
    multiple_choice_questions: List[str] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    default_checkbox_weight: float = 1.0
    default_multiple_choice_weight: float = 1.0
    algorithm: str = "hungarian"

    def to_loader_config(self) -> Dict[str, Any]:
        """Converts settings to the format required by the participant loader."""
        return {
            "id_column": self.id_column,
            "name_column": self.name_column,
            "contact_info": self.contact_info,
            "checkbox_questions": self.checkbox_questions,
            "multiple_choice_questions": self.multiple_choice_questions,
        }

    def to_scoring_config(self) -> Dict[str, Any]:
        """Converts settings to the format required by the scoring function."""
        return {
            "default_checkbox_weight": self.default_checkbox_weight,
            "default_multiple_choice_weight": self.default_multiple_choice_weight,
            "weights": self.weights,
        }


class MatchmakingEngine:
    """
    Coordinates the end-to-end matchmaking pipeline:
    - Ingests and cleans participant data from both cohorts.
    - Generates the similarity/affinity score matrix.
    - Executes the configured matching algorithm.
    - Formats match results into tabular DataFrames.
    """
    def __init__(self, config: MatchmakingConfig) -> None:
        self.config = config

    def build_score_matrix(
        self, 
        mentors: List[Participant], 
        mentees: List[Participant]
    ) -> pd.DataFrame:
        """
        Computes the pairwise compatibility score matrix between mentors (rows) and mentees (columns).
        """
        scoring_cfg = self.config.to_scoring_config()
        score_data: Dict[str, List[float]] = {}
        for mentee in mentees:
            col_scores = [compute_match_score(mentor, mentee, scoring_cfg) for mentor in mentors]
            score_data[mentee.id] = col_scores
        return pd.DataFrame(score_data, index=[m.id for m in mentors])

    def run(
        self,
        mentors_data: Union[str, pd.DataFrame],
        mentees_data: Union[str, pd.DataFrame],
    ) -> Tuple[List[Match], pd.DataFrame]:
        """
        Loads participants, builds the score matrix, and runs the configured matching algorithm.
        
        Returns:
            Tuple of (list of Match objects, score matrix DataFrame).
        """
        loader_cfg = self.config.to_loader_config()
        
        # Load mentees first to know the exact mentee count for mentor capacity allocation
        mentees = load_participants(mentees_data, loader_cfg, is_mentor=False)
        mentors = load_participants(mentors_data, loader_cfg, is_mentor=True, mentee_count=len(mentees))

        score_matrix = self.build_score_matrix(mentors, mentees)

        algo_key = self.config.algorithm.lower()
        if algo_key not in ALGORITHMS:
            available = list(ALGORITHMS.keys())
            raise ValueError(f"Unknown algorithm '{self.config.algorithm}'. Available options: {available}")

        matcher = ALGORITHMS[algo_key]()
        matches = matcher.match(mentors, mentees, score_matrix)
        return matches, score_matrix

    @staticmethod
    def format_matches_to_dataframe(
        matches: List[Match],
        group_a_label: str = "Mentor",
        group_b_label: str = "Mentee",
        contact_cols: Optional[List[str]] = None,
        detailed: bool = False,
        checkbox_questions: Optional[List[str]] = None,
        multiple_choice_questions: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Transforms a list of Match instances into a structured pandas DataFrame.
        """
        contact_cols = contact_cols or []
        checkbox_questions = checkbox_questions or []
        multiple_choice_questions = multiple_choice_questions or []

        rows: List[Dict[str, Any]] = []
        for m in matches:
            row: Dict[str, Any] = {
                group_a_label: m.mentor.name,
                group_b_label: m.mentee.name,
                "Score": m.score
            }
            # Contact fields
            for col in contact_cols:
                row[f"{group_a_label} {col}"] = m.mentor.contact_info.get(col, "N/A")
                row[f"{group_b_label} {col}"] = m.mentee.contact_info.get(col, "N/A")

            # Detailed survey answers
            if detailed:
                for q in checkbox_questions:
                    row[f"{q} ({group_a_label})"] = ", ".join(sorted(m.mentor.check_box_answers.get(q, set())))
                    row[f"{q} ({group_b_label})"] = ", ".join(sorted(m.mentee.check_box_answers.get(q, set())))
                for q in multiple_choice_questions:
                    row[f"{q} ({group_a_label})"] = m.mentor.multiple_choice_answers.get(q, "")
                    row[f"{q} ({group_b_label})"] = m.mentee.multiple_choice_answers.get(q, "")

            rows.append(row)

        return pd.DataFrame(rows)

