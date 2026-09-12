import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from src.models import Match, Participant
from src.mailer import (
    format_template, 
    EmailDispatcher, 
    send_email,
    build_contact_html,
    group_matches_by_mentor,
    build_mentor_email_context,
    build_mentee_email_context
)

def test_format_template_successful_replacement():
    """Verify template placeholders are accurately replaced with context values."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".html") as tf:
        tf.write("Hello {{name}}, your mentor is {{mentor}}!")
        tf_path = tf.name

    try:
        rendered = format_template(tf_path, {"name": "Alice", "mentor": "Bob"})
        assert rendered == "Hello Alice, your mentor is Bob!"
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

def test_format_template_raises_when_missing():
    """Verify FileNotFoundError is raised when the template file is absent."""
    with pytest.raises(FileNotFoundError, match="Template file not found at"):
        format_template("non_existent_template_path.html", {"name": "Alice"})

def test_email_dispatcher_missing_credentials():
    """Verify ValueError is raised when credentials are not supplied."""
    with pytest.raises(ValueError, match="Sender email and password must be provided"):
        EmailDispatcher("", "")

@patch("smtplib.SMTP_SSL")
def test_email_dispatcher_single_login_for_multiple_sends(mock_smtp_ssl):
    """Verify that EmailDispatcher logs in once and reuses connection across multiple sends."""
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    sender = "test@example.com"
    password = "secretpassword"

    with EmailDispatcher(sender, password, smtp_host="smtp.gmail.com", smtp_port=465) as dispatcher:
        dispatcher.send_email("student1@example.com", "Subject 1", "<p>Hello 1</p>")
        dispatcher.send_email("student2@example.com", "Subject 2", "<p>Hello 2</p>")
        dispatcher.send_email("student3@example.com", "Subject 3", "<p>Hello 3</p>")

    # Assert single connection and single login
    mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)
    mock_server.login.assert_called_once_with(sender, password)

    # Assert 3 emails sent
    assert mock_server.sendmail.call_count == 3
    # Assert connection closed
    mock_server.quit.assert_called_once()

@patch("smtplib.SMTP_SSL")
def test_send_email_convenience_function(mock_smtp_ssl):
    """Verify the backward-compatible send_email function works as expected."""
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    send_email(
        to_email="recipient@example.com",
        subject="Test Subject",
        html_body="<p>Test Body</p>",
        sender_email="sender@example.com",
        sender_password="secretpassword"
    )

    mock_server.login.assert_called_once_with("sender@example.com", "secretpassword")
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()

def test_build_contact_html():
    """Verify contact dictionary formats as clean HTML list."""
    assert build_contact_html({}) == "None provided"
    html = build_contact_html({"Phone": "12345", "Discord": "@alex"})
    assert "<li><strong>Phone:</strong> 12345</li>" in html
    assert "<li><strong>Discord:</strong> @alex</li>" in html

def test_group_matches_by_mentor():
    """Verify matches are grouped by mentor ID."""
    mentor1 = Participant("m1@test.com", "Mentor 1", {}, {}, {}, capacity=2)
    mentor2 = Participant("m2@test.com", "Mentor 2", {}, {}, {}, capacity=1)
    mentee1 = Participant("e1@test.com", "Mentee 1", {}, {}, {})
    mentee2 = Participant("e2@test.com", "Mentee 2", {}, {}, {})
    mentee3 = Participant("e3@test.com", "Mentee 3", {}, {}, {})

    matches = [
        Match(mentor1, mentee1, 4.0),
        Match(mentor1, mentee2, 3.5),
        Match(mentor2, mentee3, 5.0)
    ]

    grouped = group_matches_by_mentor(matches)
    assert len(grouped) == 2
    assert len(grouped["m1@test.com"]) == 2
    assert len(grouped["m2@test.com"]) == 1

def test_build_mentor_email_context_single_and_multi():
    """Verify context generation for single-mentee vs multi-mentee mentor."""
    mentor = Participant("sarah@test.com", "Sarah Connor", {}, {}, {"Phone": "555-0101"})
    mentee1 = Participant("peter@test.com", "Peter Parker", {}, {}, {"Phone": "555-0201"})
    mentee2 = Participant("miles@test.com", "Miles Morales", {}, {}, {"Phone": "555-0202"})

    # Single mentee context
    ctx_single = build_mentor_email_context(mentor, [Match(mentor, mentee1, 4.0)])
    assert ctx_single["mentor_name"] == "Sarah Connor"
    assert ctx_single["mentee_name"] == "Peter Parker"
    assert ctx_single["mentee_count"] == 1
    assert "555-0201" in ctx_single["mentee_contact"]

    # Multi mentee context
    ctx_multi = build_mentor_email_context(mentor, [Match(mentor, mentee1, 4.0), Match(mentor, mentee2, 3.5)])
    assert ctx_multi["mentor_name"] == "Sarah Connor"
    assert ctx_multi["mentee_name"] == "Peter Parker, Miles Morales"
    assert ctx_multi["mentee_count"] == 2
    assert "Peter Parker" in ctx_multi["mentee_contact"]
    assert "Miles Morales" in ctx_multi["mentee_contact"]
    assert "555-0201" in ctx_multi["mentee_contact"]
    assert "555-0202" in ctx_multi["mentee_contact"]

def test_build_mentee_email_context():
    """Verify mentee context contains mentor info and mentee info."""
    mentor = Participant("sarah@test.com", "Sarah Connor", {}, {}, {"Phone": "555-0101"})
    mentee = Participant("peter@test.com", "Peter Parker", {}, {}, {"Phone": "555-0201"})
    match = Match(mentor, mentee, 4.0)

    ctx = build_mentee_email_context(match)
    assert ctx["mentor_name"] == "Sarah Connor"
    assert ctx["mentor_email"] == "sarah@test.com"
    assert "555-0101" in ctx["mentor_contact"]
    assert ctx["mentee_name"] == "Peter Parker"
    assert ctx["mentee_email"] == "peter@test.com"
    assert "555-0201" in ctx["mentee_contact"]
