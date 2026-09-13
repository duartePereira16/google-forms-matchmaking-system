import io
import pandas as pd
import pytest
from src.loader import load_participants
from src.scorer import compute_match_score
from src.models import Participant

def test_checkbox_delimiter_parsing_variations():
    """Verify that checkbox questions parse comma, semicolon, and mixed delimiters into clean sets."""
    csv_data = io.StringIO(
        "Email,Name,Hobbies\n"
        "p1@test.com,Person One,\"Coding, Gym, Photography\"\n"
        "p2@test.com,Person Two,Coding;Gym;Photography\n"
        "p3@test.com,Person Three,\"Coding; Gym; Photography\"\n"
        "p4@test.com,Person Four,\" Coding , Gym ; Photography \"\n"
    )
    df = pd.read_csv(csv_data)
    config_cols = {
        "id_column": "Email",
        "name_column": "Name",
        "contact_info": [],
        "checkbox_questions": ["Hobbies"],
        "multiple_choice_questions": []
    }

    participants = load_participants(df, config_cols)
    expected_set = {"Coding", "Gym", "Photography"}

    for p in participants:
        assert isinstance(p.check_box_answers["Hobbies"], set)
        assert p.check_box_answers["Hobbies"] == expected_set

def test_load_sample_files():
    """Verify that sample CSV files load with expected participants and sets."""
    config_cols = {
        "id_column": "Email Address",
        "name_column": "Full Name",
        "contact_info": ["Phone Number"],
        "checkbox_questions": ["Hobbies", "Music Taste"],
        "multiple_choice_questions": ["Favorite Day of the Week", "Favorite Philosopher"]
    }

    freshmen = load_participants("data/inputs/freshmen.csv", config_cols, is_mentor=False)
    veterans = load_participants("data/inputs/veterans.csv", config_cols, is_mentor=True, mentee_count=len(freshmen))

    assert len(freshmen) == 7
    assert len(veterans) == 10

    peter = next(f for f in freshmen if f.name == "Peter Parker")
    sarah = next(v for v in veterans if v.name == "Sarah Connor")

    assert peter.check_box_answers["Hobbies"] == {"Photography", "Coding", "Gym"}
    assert sarah.check_box_answers["Hobbies"] == {"Coding", "Hiking", "Chess"}

    assert peter.check_box_answers["Music Taste"] == {"Pop", "Rock"}
    assert sarah.check_box_answers["Music Taste"] == {"Rock", "Jazz"}

def test_compute_match_score_with_weights():
    """Verify scoring logic for checkbox intersection and multiple choice equality."""
    p1 = Participant(
        id="1",
        name="Alice",
        check_box_answers={"Hobbies": {"Coding", "Chess", "Hiking"}},
        multiple_choice_answers={"Fav Day": "Friday", "Major": "CS"},
        contact_info={}
    )
    p2 = Participant(
        id="2",
        name="Bob",
        check_box_answers={"Hobbies": {"Coding", "Chess", "Gaming"}},
        multiple_choice_answers={"Fav Day": "Friday", "Major": "Math"},
        contact_info={}
    )

    scoring_config = {
        "default_checkbox_weight": 2.0,
        "default_multiple_choice_weight": 1.5,
        "weights": {
            "Hobbies": 3.0,
            "Fav Day": 2.0,
            "Major": 5.0
        }
    }

    # Hobbies intersection: {"Coding", "Chess"} -> 2 items * 3.0 = 6.0
    # Fav Day matches: Friday == Friday -> 1 match * 2.0 = 2.0
    # Major does not match: CS != Math -> 0.0
    # Expected total score = 8.0
    score = compute_match_score(p1, p2, scoring_config)
    assert score == pytest.approx(8.0)

def test_loader_deduplication_keeps_latest():
    """Verify that duplicate submissions for the same ID retain the latest submission."""
    csv_data = io.StringIO(
        "Email,Name,Hobbies,Day\n"
        "sarah@test.com,Sarah,Gaming,Monday\n"
        "alex@test.com,Alex,Art,Tuesday\n"
        "sarah@test.com,Sarah Connor,\"Coding, Hiking\",Friday\n"
    )
    df = pd.read_csv(csv_data)
    config_cols = {
        "id_column": "Email",
        "name_column": "Name",
        "contact_info": [],
        "checkbox_questions": ["Hobbies"],
        "multiple_choice_questions": ["Day"]
    }

    participants = load_participants(df, config_cols, deduplicate=True)
    assert len(participants) == 2

    sarah = next(p for p in participants if p.id == "sarah@test.com")
    assert sarah.name == "Sarah Connor"
    assert sarah.check_box_answers["Hobbies"] == {"Coding", "Hiking"}
    assert sarah.multiple_choice_answers["Day"] == "Friday"

def test_loader_filters_empty_and_whitespace_ids():
    """Verify that rows with null, empty, or whitespace-only IDs are safely excluded."""
    csv_data = io.StringIO(
        "Email,Name,Hobbies\n"
        ",No Email,Gaming\n"
        "   ,Whitespace Email,Art\n"
        "valid@test.com,Valid User,Reading\n"
    )
    df = pd.read_csv(csv_data)
    config_cols = {
        "id_column": "Email",
        "name_column": "Name",
        "contact_info": [],
        "checkbox_questions": ["Hobbies"],
        "multiple_choice_questions": []
    }

    participants = load_participants(df, config_cols)
    assert len(participants) == 1
    assert participants[0].id == "valid@test.com"

def test_loader_capacity_calculation_with_duplicates():
    """Verify that mentor capacities are calculated based on unique mentors, not raw duplicate rows."""
    csv_data = io.StringIO(
        "Email,Name\n"
        "m1@test.com,Mentor One (v1)\n"
        "m1@test.com,Mentor One (v2)\n"
        "m2@test.com,Mentor Two\n"
    )
    df = pd.read_csv(csv_data)
    config_cols = {
        "id_column": "Email",
        "name_column": "Name",
        "contact_info": [],
        "checkbox_questions": [],
        "multiple_choice_questions": []
    }

    # 4 mentees across 2 unique mentors -> each should get capacity 2
    mentors = load_participants(df, config_cols, is_mentor=True, mentee_count=4, deduplicate=True)
    assert len(mentors) == 2
    assert mentors[0].capacity == 2
    assert mentors[1].capacity == 2

def test_loader_missing_required_columns():
    """Verify ValueError is raised if configured ID or name column is missing."""
    df = pd.DataFrame({"WrongID": ["1"], "Name": ["A"]})
    config_cols = {
        "id_column": "Email",
        "name_column": "Name"
    }
    with pytest.raises(ValueError, match="ID column 'Email' not found"):
        load_participants(df, config_cols)
