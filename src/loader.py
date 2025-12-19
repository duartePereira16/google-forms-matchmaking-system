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
        
        interests = set()
        for col in config_cols['checkbox_questions']:
             if pd.notna(row.get(col)):
                 items = [x.strip() for x in str(row[col]).split(',')]
                 interests.update(items)
                 
        p = Participant(
            id=p_id,
            name=name,
            attributes=row.to_dict(),
            interests=interests,
            capacity=capacities[i]
        )
        participants.append(p)
        
    return participants