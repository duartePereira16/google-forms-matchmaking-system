import logging
import re
from typing import Any, Dict, List, Set, Union
import pandas as pd
from src.models import Participant

logger = logging.getLogger(__name__)

def load_participants(
    filepath_or_df: Union[str, pd.DataFrame], 
    config_cols: Dict[str, Any], 
    is_mentor: bool = False,
    mentee_count: int = 0,
    deduplicate: bool = True
) -> List[Participant]:
    """
    Loads participants from a CSV file or DataFrame into Participant domain models.
    
    Performs data cleaning:
    - Drops empty/whitespace-only IDs.
    - Deduplicates submissions by ID (keeping the latest submission).
    - Parses multi-select answers into sets of trimmed strings.
    - Trims single-select multiple choice answers.
    - Computes mentor capacity based on the ratio of mentees to mentors.
    """
    if isinstance(filepath_or_df, pd.DataFrame):
        df = filepath_or_df.copy()
    else:
        df = pd.read_csv(filepath_or_df)
    
    id_col = config_cols.get('id_column')
    name_col = config_cols.get('name_column')

    if not id_col or id_col not in df.columns:
        raise ValueError(f"ID column '{id_col}' not found in data.")
    if not name_col or name_col not in df.columns:
        raise ValueError(f"Name column '{name_col}' not found in data.")

    # --- Data Cleaning & Deduplication ---
    # Filter out null or whitespace-only IDs
    df = df[df[id_col].notna()].copy()
    df[id_col] = df[id_col].astype(str).str.strip()
    df = df[df[id_col] != ""]

    if deduplicate:
        initial_count = len(df)
        df = df.drop_duplicates(subset=[id_col], keep='last')
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.warning(
                f"Removed {dropped_count} duplicate response(s) for ID column '{id_col}'. "
                "Retained the latest submissions."
            )

    df = df.reset_index(drop=True)
    nr_participants = len(df)
    participants: List[Participant] = []

    # --- Capacity Logic ---
    capacities = [1] * nr_participants

    if is_mentor and mentee_count > 0:
        if mentee_count > nr_participants:
            base_capacity = mentee_count // nr_participants
            remainder = mentee_count % nr_participants
            for i in range(nr_participants):
                if i < remainder:
                    capacities[i] = base_capacity + 1
                else:
                    capacities[i] = base_capacity

    # --- Row Processing ---
    for i, (_, row) in enumerate(df.iterrows()):
        p_id = row[id_col]
        name = str(row[name_col]).strip()
        
        # Checkbox questions: split by comma or semicolon, trim whitespace, and store as Set[str]
        check_box_answers: Dict[str, Set[str]] = {}
        for question in config_cols.get('checkbox_questions', []):
            val = row.get(question)
            if pd.notna(val):
                items = {x.strip() for x in re.split(r'[;,]\s*', str(val)) if x.strip()}
                check_box_answers[question] = items
        
        # Multiple choice questions (both similarity and difference questions)
        multiple_choice_answers: Dict[str, str] = {}
        all_mc_questions = list(config_cols.get('multiple_choice_questions', [])) + list(config_cols.get('difference_questions', []))
        for question in all_mc_questions:
            val = row.get(question)
            if pd.notna(val):
                multiple_choice_answers[question] = str(val).strip()

        # Contact info (e.g., phone nr, email)
        contact_info: Dict[str, str] = {}
        for field in config_cols.get('contact_info', []):
            contact_info[field] = str(row.get(field, "N/A"))

        p = Participant(
            id=p_id,
            name=name,
            check_box_answers=check_box_answers,
            multiple_choice_answers=multiple_choice_answers,
            contact_info=contact_info,
            capacity=capacities[i]
        )
        participants.append(p)
        
    return participants