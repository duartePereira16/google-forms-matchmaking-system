# PairSync - Google Forms Matchmaking System 🧩

This project automates the process of matching two cohorts of people (such as senior student mentors and freshmen mentees) based on compatibility calculated from Google Forms survey responses. It is designed to maximize compatibility between members of the two groups while ensuring fairness in assignments.

A simple **Streamlit Web Application** (**PairSync**) and an interactive **CLI**, featuring dynamic CSV mapping, visual results, and built-in email notification sending.

---

## Features

- **Interactive Web UI & Rich CLI**: Upload your CSVs, map your columns visually or in the terminal, and generate matches in seconds.
- **Flexible Data Mapping**: Works with *any* form structure. Ingests standard Google Forms exports (handling both comma and semicolon checkbox delimiters).
- **Multiple Algorithms**: Choose between **Hungarian** (mathematically optimal global score), **Global Greedy** (highest-scoring pairs first), or **Iterative Greedy** (mentee-sequential selection).
- **Dynamic Weight Scoring**: Assign custom weights to Checkbox (set intersection) or Multiple Choice (exact match) questions.
- **Automated Deduplication**: Automatically detects multiple submissions from the same student ID/email and retains their latest response.
- **Integrated Email Dispatcher**: Send personalized HTML emails directly to both groups with persistent SMTP sessions and consolidated multi-mentee emails for mentors with capacity > 1.
- **Dockerized**: Zero-setup deployment using Docker Compose.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (or [Docker Desktop](https://www.docker.com/products/docker-desktop/) / Docker Compose).
- Exported CSV files from your two Google Forms.
- *(Optional)* A Google Account with an App Password if you plan to send emails directly.

---

### Option A: Web UI via Docker Compose
```bash
git clone https://github.com/duartePereira16/google-forms-matchmaking-system.git
cd google-forms-matchmaking-system

# (Optional) Pre-configure your Gmail credentials
cp .env.example .env

# Build and launch with Docker
docker compose up --build
```
Access the web application in your browser at `http://localhost:8501`.

---

### Option B: Web UI directly via Virtual Environment
If you prefer running Streamlit natively on your machine without Docker:

```bash
git clone https://github.com/duartePereira16/google-forms-matchmaking-system.git
cd google-forms-matchmaking-system

# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies (using pip or uv)
pip install -r requirements.txt
# Or with uv: uv pip install -r requirements.txt

# 3. (Optional) Set up your credentials
cp .env.example .env

# 4. Launch the Streamlit Web UI
streamlit run app.py
```
The app will open automatically at `http://localhost:8501`.

---

### Option C: Interactive Terminal CLI
If you prefer a keyboard-driven terminal interface:

```bash
# Ensure your virtual environment is active and dependencies installed
python cli.py
```
The CLI guides you through the exact same workflow with interactive arrow-key navigation!

---

## The Workflow

1. **Upload Data**: Load your Group A (Mentors) and Group B (Mentees) CSV files.
2. **Identity Mapping**: Select which columns correspond to the participant's ID (e.g., Email), Full Name, and Contact Information (e.g., phone number, social handles).
3. **Question Mapping**: Classify remaining columns as **Checkbox**, **Multiple Choice** (scores when identical), **Multiple Choice (Opposites)** (scores when answers differ), or **Exclude**, and adjust priority weights.
4. **Execute**: Pick your matching algorithm (**Hungarian**, **Iterative Greedy**, or **Greedy**) and click **Generate Matches**.
5. **Review & Export**: Inspect the match table, toggle the detailed view with full survey responses, download `matches.csv`, and preview email templates with real data.
6. **Dispatch Emails**: Click "Configure & Send Emails" to dispatch personalized emails via Gmail SMTP using a Google App Password.

---

## Email Configuration Setup

To use the built-in email dispatcher with Gmail, generate an **App Password**:

1. Go to your [Google Account Manage page](https://myaccount.google.com/).
2. On the left navigation panel, click **Security**.
3. Under "How you sign in to Google", ensure **2-Step Verification** is turned ON.
4. Click on **2-Step Verification**, scroll to the bottom, and select **App passwords**.
5. Give it a name (e.g., "PairSync") and click **Create**.
6. Copy the generated 16-character password into your `.env` file or directly into the app prompt.

```bash
# In .env
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your16charpassword
```

---

## Customizing Email Templates

You can add or customize email designs in `src/templates/`:
1. Create a folder for your theme (e.g., `src/templates/my-theme/`).
2. Add your HTML templates:
   - `mentor_template.html`: Sent to mentors assigned a single mentee.
   - `mentee_template.html`: Sent to mentees.
   - `multi_mentor_template.html` *(Optional)*: Dedicated template sent to mentors assigned 2 or more mentees (e.g., customized cohort/group instructions). If omitted, the system seamlessly falls back to `mentor_template.html`.
   - `mentee_card_template.html` *(Optional)*: Sub-template defining the layout, language labels (`Nome:` vs `Name:`), and border styling for each mentee card when rendered inside `{{mentee_cards}}`. If omitted, a clean generic card is used.
3. The application will automatically detect your new theme in the dropdown menu.

### Supported Placeholders
| Placeholder | Description |
| :--- | :--- |
| `{{mentor_name}}` | Full name of the mentor |
| `{{mentor_email}}` | ID / Email of the mentor |
| `{{mentor_contact}}` | HTML formatted contact info for the mentor |
| `{{mentee_name}}` | Full name of the mentee (or comma-separated names if mentor has $>1$ mentees) |
| `{{mentee_email}}` | ID / Email of the mentee (or comma-separated emails) |
| `{{mentee_contact}}` | HTML formatted contact info (or consolidated contact cards for multi-mentee mentors) |
| `{{mentee_cards}}` | Individual styled HTML cards for each mentee (Name + Contacts, without email) |
| `{{mentee_count}}` | Number of mentees assigned to the mentor (available in mentor templates) |

---

## Running Automated Tests

To run the complete unit test suite:
```bash
pytest -v
```
