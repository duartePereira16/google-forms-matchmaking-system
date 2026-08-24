# Google Forms Matchmaking System 🧩

This project automates the process of matching two groups of people based on their answers to Google Forms. It is designed to maximize compatibility between members of the two groups while ensuring fairness in assignments.

Originally a simple script, it has evolved into a fully-fledged **Streamlit Web Application** featuring dynamic drag-and-drop CSV mapping, visual results, and built-in email notification sending.

---

## Features

- **Interactive Web UI**: No coding or configuration files required. Upload your CSVs, map your columns visually, and generate matches in seconds.
- **Flexible Data Mapping**: Automatically cross-references headers from both Google Forms. Works with *any* form structure.
- **Multiple Algorithms**: Choose between **Global Greedy**, **Iterative Greedy**, or the mathematically optimal **Hungarian** strategy.
- **Dynamic Weight Scoring**: Assign custom weights to every single Checkbox (intersection matching) or Multiple Choice (exact match) question instantly from the UI.
- **Integrated Email Notifier**: Review matches and send beautifully templated HTML emails directly to Mentors and Mentees in one click (with a safe "Dry Run" mode).
- **Dockerized**: Zero-setup deployment using Docker Compose.

---

## Getting Started

The easiest and recommended way to run this application is using Docker.

### 1. Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Compose.
- Ensure you have your exported CSV files from your two Google Forms.

### 2. Launch the Application
```bash
git clone https://github.com/duartePereira16/google-forms-matchmaking-system.git
cd google-forms-matchmaking-system

# Build and start the web server
docker-compose up --build
```
The Matchmaking UI will instantly be available in your browser at `http://localhost:8501`.

### 3. Email Configuration
If you want to use the built-in email notifier to send matches to participants the app needs to log into a Gmail account. Google no longer allows simple password logins for scripts, so you must generate an **App Password**.

### Tutorial: How to get an App Password
1. Go to your [Google Account Manage page](https://myaccount.google.com/).
2. On the left navigation panel, click **Security**.
3. Under the "How you sign in to Google" section, ensure **2-Step Verification** is turned ON. (You cannot generate an App Password without this).
4. Click on **2-Step Verification**, scroll to the bottom, and click on **App passwords**.
5. Give it a name (e.g., "Matchmaker") and click **Create**.
6. Google will give you a 16-character password in a yellow box. **Copy this password**.

### Setting up the `.env` file
1. Create a new file named `.env` in the root folder of this project (right next to this README).
2. Add your email and the 16-character App Password (without spaces) like this:

```
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop
```
*Note: Make sure not to put quotes around the email or password.*

---

## The Workflow

1. **Upload Data**: Drag and drop your Group A and Group B CSV files into the browser.
2. **Identity Mapping**: Tell the system which columns correspond to the participant's Name, Email, and extra Contact Info.
3. **Question Mapping**: All remaining columns are treated as questions. You simply specify if they are a Checkbox or Multiple Choice question, and assign a priority weight.
4. **Execute**: Pick your algorithm and click Generate.
5. **Review & Send**: View the matched table in the browser. You can download the results as a CSV, preview the actual HTML emails with real data, and click "Send".

---

## CLI Usage (Legacy)
If you prefer running the logic headlessly without the UI, you can still use the Python CLI.

```bash
# Set up a virtual environment
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the CLI using a config file (see config.example.json)
python -m src.main --config config.example.json
```

**config.example.json:**

```json
{
    "labels": {
        "group_a": "Veteran",
        "group_b": "Freshman"
    },
    "files": {
        "group_a": "data/inputs/veterans.csv",
        "group_b": "data/inputs/freshmen.csv",
        "output": "data/outputs/matches.csv"
    },
    "columns": {
        "id_column": "Email Address",
        "name_column": "Full Name",
        "contact_info": [
            "Email Address",
            "Phone Number"
        ],
        "checkbox_questions": [
            "Hobbies",
            "Music Taste"
        ],
        "multiple_choice_questions": [
            "Favorite Day of the Week",
            "Favorite Philosopher"
        ]
    },
    "scoring": {
        "default_checkbox_weight": 1.0,
        "default_multiple_choice_weight": 2.0,
        "weights": {
            "Favorite Philosopher": 4.0,
            "Music Taste": 3.0
        }
    },
    "algorithm": "hungarian",
    "notifications": {
        "send_to_group_a": true,
        "send_to_group_b": true,
        "mentor_template": "src/templates/mentor_template.html",
        "mentee_template": "src/templates/mentee_template.html"
    }
}
```


---
