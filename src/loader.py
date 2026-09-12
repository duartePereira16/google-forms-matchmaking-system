import re
from typing import Any, Dict, List, Set, Union
import pandas as pd
from src.models import Participant

def load_participants(
    filepath_or_df: Union[str, pd.DataFrame], 
    config_cols: Dict[str, Any], 
    is_mentor: bool = False,
    mentee_count: int = 0
) -> List[Participant]:
    """
    Loads participants from a CSV file or DataFrame into Participant domain models.
    
    Parses checkbox questions into sets of strings (handling standard Google Forms
    comma-separated format as well as semicolon-delimited lists), multiple choice questions
    as trimmed strings, and assigns mentor capacity when applicable.
    """
    if isinstance(filepath_or_df, pd.DataFrame):
        df = filepath_or_df
    else:
        df = pd.read_csv(filepath_or_df)
    
    participants: List[Participant] = []
    nr_participants = len(df)
    
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
        p_id = str(row[config_cols['id_column']]).strip()
        name = str(row[config_cols['name_column']]).strip()
        
        # Checkbox questions: split by comma or semicolon, trim whitespace, and store as Set[str]
        check_box_answers: Dict[str, Set[str]] = {}
        for question in config_cols.get('checkbox_questions', []):
            val = row.get(question)
            if pd.notna(val):
                items = {x.strip() for x in re.split(r'[;,]\s*', str(val)) if x.strip()}
                check_box_answers[question] = items
        
        # Multiple choice questions
        multiple_choice_answers: Dict[str, str] = {}
        for question in config_cols.get('multiple_choice_questions', []):
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