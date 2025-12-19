from dataclasses import dataclass
from typing import Dict, Set

@dataclass(frozen=True)
class Participant:
    id: str                                         # Unique ID (e.g., Email)
    name: str
    check_box_answers: Dict[str, Set[str]]          # question name -> set of answers
    multiple_choice_answers: Dict[str, str]         # question name -> answer    
    contact_info: Dict[str, str]                    # field name -> info (e.g., email, phone)
    capacity: int = 1

@dataclass(frozen=True)
class Match:
    mentor: Participant
    mentee: Participant
    score: float