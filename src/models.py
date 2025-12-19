from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass(frozen=True)
class Participant:
    id: str                     # Unique ID (e.g., Email)
    name: str
    attributes: Dict[str, str]  # Raw answers for multiple choice
    interests: Set[str]         # Parsed set for checkboxes (e.g., {"Music", "Sports"})
    capacity: int = 1           # How many people can they be matched with?

@dataclass(frozen=True)
class Match:
    mentor: Participant
    mentee: Participant
    score: float