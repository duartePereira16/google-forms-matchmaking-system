import pandas as pd
from typing import List
from src.models import Participant

def load_participants(
    filepath: str, 
    config_cols: dict, 
    is_mentor: bool = False,
    mentee_count: int = 0  # <--- This argument is required by the new main.py
) -> List[Participant]:
    
    df = pd.read_csv(filepath)
    participants = []
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
        p_id = row[config_cols['id_column']]
        name = row[config_cols['name_column']]
        
        # check box questions
        check_box_answers = {}
        for question in config_cols['checkbox_questions']:
             if pd.notna(row.get(question)):
                 items = [x.strip() for x in str(row[question]).split(',')]
                 check_box_answers[question] = items
        
        # multiple choice questions
        multiple_choice_answers = {}
        for question in config_cols['multiple_choice_questions']:
            if pd.notna(row.get(question)):
                multiple_choice_answers[question] = str(row[question]).strip()

        # contact info (phone nr, email)
        contact_info = {}
        for field in config_cols['contact_info']:
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