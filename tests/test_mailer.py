import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from src.models import Match, Participant
from src.mailer import (
    format_template, 
    EmailDispatcher, 
    send_email,
    resolve_mentor_template_path,
    build_contact_html,
    group_matches_by_mentor,
    render_mentee_cards,
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

    # Multi mentee context (default theme -> Name/Contacts)
    ctx_multi = build_mentor_email_context(mentor, [Match(mentor, mentee1, 4.0), Match(mentor, mentee2, 3.5)])
    assert ctx_multi["mentor_name"] == "Sarah Connor"
    assert ctx_multi["mentee_name"] == "Peter Parker, Miles Morales"
    assert ctx_multi["mentee_count"] == 2
    assert "Peter Parker" in ctx_multi["mentee_contact"]
    assert "Miles Morales" in ctx_multi["mentee_contact"]
    assert "555-0201" in ctx_multi["mentee_contact"]
    assert "555-0202" in ctx_multi["mentee_contact"]
    # Verify email is not included next to the name
    assert "peter@test.com" not in ctx_multi["mentee_contact"]
    assert "miles@test.com" not in ctx_multi["mentee_contact"]
    assert "Name:" in ctx_multi["mentee_contact"]
    assert "Contacts:" in ctx_multi["mentee_contact"]
    assert ctx_multi["mentee_cards"] == ctx_multi["mentee_contact"]

    # Multi mentee context (fct-unio Portuguese theme -> Nome/Contactos and orange border from sub-template)
    ctx_pt = build_mentor_email_context(mentor, [Match(mentor, mentee1, 4.0), Match(mentor, mentee2, 3.5)], theme_dir="src/templates/fct-unio")
    assert "Nome:" in ctx_pt["mentee_cards"]
    assert "Contactos:" in ctx_pt["mentee_cards"]
    assert "peter@test.com" not in ctx_pt["mentee_cards"]
    assert "#f18e0c" in ctx_pt["mentee_cards"]

def test_render_mentee_cards_custom_subtemplate(tmp_path):
    """Verify render_mentee_cards respects a custom theme's mentee_card_template.html."""
    custom_card = tmp_path / "mentee_card_template.html"
    custom_card.write_text('<div class="custom-card">Hi {{mentee_name}}! Reach out: {{mentee_contact}}</div>')

    mentee = Participant("charlie@test.com", "Charlie", {}, {}, {"Telegram": "@charlie"})
    rendered = render_mentee_cards([mentee], theme_dir=str(tmp_path))

    assert "custom-card" in rendered
    assert "Hi Charlie!" in rendered
    assert "@charlie" in rendered
    assert "charlie@test.com" not in rendered

def test_render_mentee_cards_fallback(tmp_path):
    """Verify render_mentee_cards gracefully uses fallback when mentee_card_template.html is absent."""
    mentee = Participant("diana@test.com", "Diana", {}, {}, {"Phone": "123"})
    rendered = render_mentee_cards([mentee], theme_dir=str(tmp_path))

    assert "mentee-card" in rendered
    assert "Diana" in rendered
    assert "123" in rendered

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

def test_resolve_mentor_template_path_single(tmp_path):
    """When mentee_count <= 1, mentor_template.html should be resolved."""
    single_tpl = tmp_path / "mentor_template.html"
    single_tpl.write_text("Single mentee template")
    multi_tpl = tmp_path / "multi_mentor_template.html"
    multi_tpl.write_text("Multi mentee template")

    resolved = resolve_mentor_template_path(str(tmp_path), mentee_count=1)
    assert resolved == str(single_tpl)

def test_resolve_mentor_template_path_multi_when_available(tmp_path):
    """When mentee_count > 1 and multi_mentor_template.html exists, it should be resolved."""
    single_tpl = tmp_path / "mentor_template.html"
    single_tpl.write_text("Single mentee template")
    multi_tpl = tmp_path / "multi_mentor_template.html"
    multi_tpl.write_text("Multi mentee template")

    resolved = resolve_mentor_template_path(str(tmp_path), mentee_count=3)
    assert resolved == str(multi_tpl)

def test_resolve_mentor_template_path_multi_fallback_when_missing(tmp_path):
    """When mentee_count > 1 but multi_mentor_template.html does NOT exist, fall back to mentor_template.html."""
    single_tpl = tmp_path / "mentor_template.html"
    single_tpl.write_text("Single mentee template")

    resolved = resolve_mentor_template_path(str(tmp_path), mentee_count=2)
    assert resolved == str(single_tpl)

