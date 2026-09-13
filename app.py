import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from src.engine import MatchmakingConfig, MatchmakingEngine
from src.strategies import ALGORITHMS
from src.mailer import (
    format_template, 
    send_email, 
    EmailDispatcher,
    resolve_mentor_template_path,
    group_matches_by_mentor,
    build_mentor_email_context,
    build_mentee_email_context
)

st.set_page_config(page_title="Matchmaker", page_icon="🧩", layout="wide")

st.title("🧩 PairSync")
st.markdown("Upload your forms, configure your questions, and automatically match Mentors with Mentees.")

# --- Session State Initialization ---
if 'step' not in st.session_state:
    st.session_state.step = 1

def next_step(step):
    st.session_state.step = step

if 'matches' not in st.session_state:
    st.session_state.matches = None
    
if 'config_cols' not in st.session_state:
    st.session_state.config_cols = None

# --- Step 1: Data Upload ---
st.header("Step 1: Upload Data & Labels")
col1, col2 = st.columns(2)
with col1:
    group_a_label = st.text_input("Group A Label", value="Mentor")
    group_a_file = st.file_uploader(f"Upload {group_a_label} CSV", type=["csv"])
with col2:
    group_b_label = st.text_input("Group B Label", value="Mentee")
    group_b_file = st.file_uploader(f"Upload {group_b_label} CSV", type=["csv"])

df_a = None
df_b = None

if group_a_file and group_b_file:
    try:
        df_a = pd.read_csv(group_a_file)
        df_b = pd.read_csv(group_b_file)
        
        if df_a.empty or df_b.empty:
            st.error("One or both of the CSV files are empty.")
            st.stop()
        elif list(df_a.columns) != list(df_b.columns):
            st.error("The column headers in both CSVs must be perfectly identical.")
            st.stop()
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Preview: {group_a_label} Data**")
                st.dataframe(df_a.head(), use_container_width=True)
            with col_b:
                st.markdown(f"**Preview: {group_b_label} Data**")
                st.dataframe(df_b.head(), use_container_width=True)
            
            if st.session_state.step == 1:
                st.button("Confirm Data Upload", on_click=next_step, args=(2,), type="primary")
    except Exception as e:
        st.error(f"Error parsing CSVs: {e}")
        st.stop()
else:
    st.info("Please upload both CSV files to continue.")
    st.stop()

if st.session_state.step < 2:
    st.stop()


# --- Step 2: Identity Mapping ---
st.divider()
st.header("Step 2: Identity Mapping")
columns = list(df_a.columns)

col1, col2 = st.columns(2)
with col1:
    id_col = st.selectbox("ID Column (e.g., Email)", columns)
    name_col = st.selectbox("Name Column", columns, index=1 if len(columns) > 1 else 0)
with col2:
    contact_cols = st.multiselect("Additional Contact Info Columns", columns)

if st.session_state.step == 2:
    st.button("Confirm Identity Mapping", on_click=next_step, args=(3,), type="primary")

selected_identity_cols = set([id_col, name_col] + contact_cols)
question_cols = [c for c in columns if c not in selected_identity_cols]

if st.session_state.step < 3:
    st.stop()


# --- Step 3: Question Configuration ---
st.divider()
st.header("Step 3: Question Configuration")
st.markdown("Select the question type and set the appropriate weight for each question.")

# Initialize question states
for q in question_cols:
    if f"type_{q}" not in st.session_state:
        st.session_state[f"type_{q}"] = "Checkbox"
    if f"weight_{q}" not in st.session_state:
        st.session_state[f"weight_{q}"] = 1.0

def update_global_cb():
    new_w = st.session_state.global_cb_weight_input
    for q in question_cols:
        if st.session_state[f"type_{q}"] == 'Checkbox':
            st.session_state[f"weight_{q}"] = new_w

def update_global_mc():
    new_w = st.session_state.global_mc_weight_input
    for q in question_cols:
        if st.session_state[f"type_{q}"] == 'Multiple Choice':
            st.session_state[f"weight_{q}"] = new_w

def on_type_change(q):
    new_type = st.session_state[f"type_{q}"]
    if new_type == 'Checkbox':
        st.session_state[f"weight_{q}"] = st.session_state.global_cb_weight_input
    elif new_type == 'Multiple Choice':
        st.session_state[f"weight_{q}"] = st.session_state.global_mc_weight_input
    else:
        st.session_state[f"weight_{q}"] = 0.0

col1, col2 = st.columns(2)
with col1:
    st.number_input("Global Checkbox Weight", value=1.0, step=0.5, key="global_cb_weight_input", on_change=update_global_cb)
with col2:
    st.number_input("Global Multiple Choice Weight", value=1.0, step=0.5, key="global_mc_weight_input", on_change=update_global_mc)

st.subheader("Individual Questions")

for q in question_cols:
    q_name, q_type, q_weight = st.columns([2, 1, 1])
    with q_name:
        st.markdown(f"#### {q}")
    with q_type:
        st.selectbox("Type", ['Checkbox', 'Multiple Choice', 'Exclude'], key=f"type_{q}", label_visibility="collapsed", on_change=on_type_change, args=(q,))
    with q_weight:
        disabled = (st.session_state[f"type_{q}"] == 'Exclude')
        st.number_input("Weight", step=0.5, key=f"weight_{q}", disabled=disabled, label_visibility="collapsed")
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 10px;'/>", unsafe_allow_html=True)

active_questions = [q for q in question_cols if st.session_state[f"type_{q}"] != 'Exclude']
if not active_questions:
    st.warning("Please include at least one question to run the matcher.")
    st.stop()

if st.session_state.step == 3:
    st.button("Confirm Configuration", on_click=next_step, args=(4,), type="primary")

if st.session_state.step < 4:
    st.stop()


# --- Step 4: Algorithm & Execution ---
st.divider()
st.header("Step 4: Algorithm & Execution")

col_algo, col_info, col_btn = st.columns([1, 2, 1])
with col_algo:
    algo = st.selectbox("Algorithm", list(ALGORITHMS.keys()), index=0)
with col_info:
    st.info(
        "**Available Algorithms:**\n"
        "- **Hungarian:** Guarantees the highest mathematically possible *global* score for the entire group. (Fairest overall)\n"
        "- **Iterative Greedy:** A balanced middle-ground that assigns the current absolute highest scoring pair step-by-step.\n"
        "- **Greedy:** Simple fast iteration picking the best available match for each individual in order."
    )

with col_btn:
    st.write("") 
    st.write("") 
    if st.button("Generate Matches", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            checkbox_qs = [q for q in question_cols if st.session_state[f"type_{q}"] == 'Checkbox']
            mc_qs = [q for q in question_cols if st.session_state[f"type_{q}"] == 'Multiple Choice']
            weights = {
                q: st.session_state[f"weight_{q}"] 
                for q in question_cols 
                if st.session_state[f"type_{q}"] in ['Checkbox', 'Multiple Choice']
            }
                    
            match_config = MatchmakingConfig(
                id_column=id_col,
                name_column=name_col,
                contact_info=contact_cols,
                checkbox_questions=checkbox_qs,
                multiple_choice_questions=mc_qs,
                weights=weights,
                default_checkbox_weight=st.session_state.global_cb_weight_input,
                default_multiple_choice_weight=st.session_state.global_mc_weight_input,
                algorithm=algo
            )

            engine = MatchmakingEngine(match_config)
            matches, score_df = engine.run(df_a, df_b)
            
            st.session_state.matches = matches
            st.session_state.match_config = match_config
            st.session_state.step = 5

if not st.session_state.matches:
    st.stop()

st.success(f"Successfully generated {len(st.session_state.matches)} matches!")

show_detailed = st.toggle("Show Detailed View")

cfg = st.session_state.match_config
res_df = MatchmakingEngine.format_matches_to_dataframe(
    st.session_state.matches,
    group_a_label=group_a_label,
    group_b_label=group_b_label,
    contact_cols=cfg.contact_info,
    detailed=show_detailed,
    checkbox_questions=cfg.checkbox_questions,
    multiple_choice_questions=cfg.multiple_choice_questions
)
st.dataframe(res_df, use_container_width=True)

csv = res_df.to_csv(index=False).encode('utf-8')
st.download_button("Download Matches CSV", csv, "matches.csv", "text/csv")


if st.session_state.step < 5:
    st.stop()

# --- Step 5: Email Notification Setup ---
st.divider()
st.header("Step 5: Email Notifications")
st.markdown("Send HTML emails to the matched participants.")

template_dirs = [d for d in os.listdir("src/templates") if os.path.isdir(os.path.join("src/templates", d))]
if not template_dirs:
    st.error("No template directories found in `src/templates/`.")
    st.stop()

selected_theme = st.selectbox("Template Theme", template_dirs)

col1, col2 = st.columns(2)
with col1:
    send_mentors = st.checkbox(f"Send to {group_a_label}s", value=True)
with col2:
    send_mentees = st.checkbox(f"Send to {group_b_label}s", value=True)


st.subheader("Email Preview")
grouped_mentors = group_matches_by_mentor(st.session_state.matches)
theme_dir = os.path.join("src/templates", selected_theme)

preview_col1, preview_col2 = st.columns(2)

with preview_col1:
    if send_mentors:
        st.markdown(f"**{group_a_label} Template Preview**")
        mentor_options = list(grouped_mentors.keys())
        selected_m_id = st.selectbox(
            f"Select {group_a_label} to preview", 
            options=mentor_options, 
            format_func=lambda mid: f"{grouped_mentors[mid][0].mentor.name} ({len(grouped_mentors[mid])} {group_b_label}{'s' if len(grouped_mentors[mid]) > 1 else ''})"
        )
        m_list = grouped_mentors[selected_m_id]
        mentor_obj = m_list[0].mentor
        mentor_ctx = build_mentor_email_context(mentor_obj, m_list, theme_dir=theme_dir)
        mentor_tpl_path = resolve_mentor_template_path(theme_dir, len(m_list))

        if os.path.exists(mentor_tpl_path):
            html_preview = format_template(mentor_tpl_path, mentor_ctx)
            st.components.v1.html(html_preview, height=420, scrolling=True)
        else:
            st.error(f"Missing template: {mentor_tpl_path}")

with preview_col2:
    if send_mentees:
        st.markdown(f"**{group_b_label} Template Preview**")
        mentee_options = list(range(len(st.session_state.matches)))
        selected_idx = st.selectbox(
            f"Select {group_b_label} to preview",
            options=mentee_options,
            format_func=lambda idx: st.session_state.matches[idx].mentee.name
        )
        match_obj = st.session_state.matches[selected_idx]
        mentee_ctx = build_mentee_email_context(match_obj)
        mentee_tpl_path = os.path.join(theme_dir, "mentee_template.html")

        if os.path.exists(mentee_tpl_path):
            html_preview = format_template(mentee_tpl_path, mentee_ctx)
            st.components.v1.html(html_preview, height=420, scrolling=True)
        else:
            st.error(f"Missing template: {mentee_tpl_path}")


@st.dialog("Enter Email Credentials")
def email_credentials_dialog():
    st.markdown("Enter your Gmail address and 16-character App Password to send emails.")
    default_email = os.getenv("SENDER_EMAIL", "")
    default_password = os.getenv("SENDER_PASSWORD", "")
    sender_email_input = st.text_input("Sender Email Address", value=default_email)
    sender_password_input = st.text_input("App Password", value=default_password, type="password")
    
    if st.button("Confirm & Send"):
        if not sender_email_input or not sender_password_input:
            st.error("Please provide both the Sender Email and App Password.")
        else:
            with st.spinner("Sending emails..."):
                success_count = 0
                error_count = 0
                grouped_by_mentor = group_matches_by_mentor(st.session_state.matches)
                try:
                    with EmailDispatcher(sender_email_input, sender_password_input) as dispatcher:
                        # 1. Send consolidated emails to mentors using appropriate single or multi template
                        if send_mentors:
                            for mentor_id, m_list in grouped_by_mentor.items():
                                mentor = m_list[0].mentor
                                m_ctx = build_mentor_email_context(mentor, m_list, theme_dir=theme_dir)
                                mentor_tpl_path = resolve_mentor_template_path(theme_dir, len(m_list))
                                if os.path.exists(mentor_tpl_path):
                                    try:
                                        html_body = format_template(mentor_tpl_path, m_ctx)
                                        dispatcher.send_email(mentor.id, f"Matchmaking Result - {group_a_label}", html_body)
                                        success_count += 1
                                    except Exception as e:
                                        error_count += 1
                                        st.error(f"Error sending to {mentor.id}: {e}")
                                else:
                                    error_count += 1
                                    st.error(f"Missing template: {mentor_tpl_path}")
                        
                        # 2. Send emails to mentees
                        if send_mentees and os.path.exists(os.path.join(theme_dir, "mentee_template.html")):
                            mentee_tpl_path = os.path.join(theme_dir, "mentee_template.html")
                            for m in st.session_state.matches:
                                m_ctx = build_mentee_email_context(m)
                                try:
                                    html_body = format_template(mentee_tpl_path, m_ctx)
                                    dispatcher.send_email(m.mentee.id, f"Matchmaking Result - {group_b_label}", html_body)
                                    success_count += 1
                                except Exception as e:
                                    error_count += 1
                                    st.error(f"Error sending to {m.mentee.id}: {e}")
                except Exception as e:
                    st.error(f"SMTP Connection Error: {e}")
                
                if error_count == 0 and success_count > 0:
                    st.success(f"Successfully sent {success_count} emails!")
                elif error_count > 0:
                    st.warning(f"Sent {success_count} emails, but encountered {error_count} errors.")


if send_mentors or send_mentees:
    if st.button("Configure & Send Emails", type="primary"):
        email_credentials_dialog()
else:
    st.info("Please select at least one group to send emails to.")
