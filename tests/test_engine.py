import pytest
import pandas as pd
from src.engine import MatchmakingConfig, MatchmakingEngine
from src.models import Match, Participant

def test_matchmaking_config_conversion():
    """Verify config mapping to loader and scoring formats."""
    config = MatchmakingConfig(
        id_column="Email",
        name_column="Name",
        contact_info=["Phone"],
        checkbox_questions=["Hobbies"],
        multiple_choice_questions=["Day"],
        weights={"Hobbies": 2.0},
        default_checkbox_weight=1.5,
        default_multiple_choice_weight=1.0,
        algorithm="greedy"
    )

    loader_cfg = config.to_loader_config()
    assert loader_cfg["id_column"] == "Email"
    assert loader_cfg["name_column"] == "Name"
    assert loader_cfg["contact_info"] == ["Phone"]
    assert loader_cfg["checkbox_questions"] == ["Hobbies"]
    assert loader_cfg["multiple_choice_questions"] == ["Day"]

    scoring_cfg = config.to_scoring_config()
    assert scoring_cfg["default_checkbox_weight"] == 1.5
    assert scoring_cfg["default_multiple_choice_weight"] == 1.0
    assert scoring_cfg["weights"] == {"Hobbies": 2.0}

def test_engine_run_sample_data():
    """Verify end-to-end matchmaking execution using MatchmakingEngine."""
    config = MatchmakingConfig(
        id_column="Email Address",
        name_column="Full Name",
        contact_info=["Phone Number"],
        checkbox_questions=["Hobbies", "Music Taste"],
        multiple_choice_questions=["Favorite Day of the Week", "Favorite Philosopher"],
        algorithm="hungarian"
    )

    engine = MatchmakingEngine(config)
    matches, score_df = engine.run("data/inputs/veterans.csv", "data/inputs/freshmen.csv")

    assert len(matches) == 7
    assert score_df.shape == (10, 7)
    for m in matches:
        assert m.score > 0
        assert m.mentor.name != ""
        assert m.mentee.name != ""

def test_engine_unknown_algorithm_raises():
    """Verify ValueError is raised when an unsupported algorithm is provided."""
    config = MatchmakingConfig(
        id_column="Email Address",
        name_column="Full Name",
        algorithm="invalid_algo"
    )
    engine = MatchmakingEngine(config)
    with pytest.raises(ValueError, match="Unknown algorithm 'invalid_algo'"):
        engine.run("data/inputs/veterans.csv", "data/inputs/freshmen.csv")

def test_engine_format_matches_to_dataframe():
    """Verify DataFrame formatting for standard and detailed view."""
    mentor = Participant(
        id="m@test.com",
        name="Sarah",
        check_box_answers={"Hobbies": {"Coding", "Hiking"}},
        multiple_choice_answers={"Day": "Friday"},
        contact_info={"Phone": "111"}
    )
    mentee = Participant(
        id="e@test.com",
        name="Peter",
        check_box_answers={"Hobbies": {"Coding", "Gym"}},
        multiple_choice_answers={"Day": "Friday"},
        contact_info={"Phone": "222"}
    )
    matches = [Match(mentor, mentee, 4.0)]

    # Standard format
    df_std = MatchmakingEngine.format_matches_to_dataframe(
        matches,
        group_a_label="Mentor",
        group_b_label="Mentee",
        contact_cols=["Phone"]
    )
    assert len(df_std) == 1
    assert df_std.loc[0, "Mentor"] == "Sarah"
    assert df_std.loc[0, "Mentee"] == "Peter"
    assert df_std.loc[0, "Score"] == 4.0
    assert df_std.loc[0, "Mentor Phone"] == "111"
    assert df_std.loc[0, "Mentee Phone"] == "222"
    assert "Hobbies (Mentor)" not in df_std.columns

    # Detailed format
    df_det = MatchmakingEngine.format_matches_to_dataframe(
        matches,
        group_a_label="Mentor",
        group_b_label="Mentee",
        contact_cols=["Phone"],
        detailed=True,
        checkbox_questions=["Hobbies"],
        multiple_choice_questions=["Day"]
    )
    assert "Hobbies (Mentor)" in df_det.columns
    assert df_det.loc[0, "Hobbies (Mentor)"] == "Coding, Hiking"
    assert df_det.loc[0, "Hobbies (Mentee)"] == "Coding, Gym"
    assert df_det.loc[0, "Day (Mentor)"] == "Friday"
    assert df_det.loc[0, "Day (Mentee)"] == "Friday"

