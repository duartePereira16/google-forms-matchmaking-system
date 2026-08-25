# Google Forms Matchmaking System 🧩

This project automates the process of matching two groups of people based on their answers to Google Forms. It is designed to maximize compatibility between members of the two groups while ensuring fairness in assignments.

Originally a simple script, it has evolved into a fully-fledged **Streamlit Web Application** featuring dynamic drag-and-drop CSV mapping, visual results, and built-in email notification sending.

---

## Features

- **Interactive Web UI**: No coding or configuration files required. Upload your CSVs, map your columns visually, and generate matches in seconds.
- **Flexible Data Mapping**: Automatically cross-references headers from both Google Forms. Works with *any* form structure.
- **Multiple Algorithms**: Choose between **Global Greedy**, **Iterative Greedy**, or the mathematically optimal **Hungarian** strategy.
- **Dynamic Weight Scoring**: Assign custom weights to every single Checkbox (intersection matching) or Multiple Choice (exact match) question instantly from the UI.
- **Integrated Email Notifier**: Review matches and emails directly to both groups in one click.
- **Dockerized**: Zero-setup deployment using Docker Compose.

---

## Getting Started

The easiest and recommended way to run this application is using Docker.

### 1. Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Compose.
- Ensure you have your exported CSV files from your two Google Forms. Both CSV files **must** have identical column headers.

### 2. Launch the Application
```bash
git clone https://github.com/duartePereira16/google-forms-matchmaking-system.git
cd google-forms-matchmaking-system

# Build and start the web server
docker-compose up --build
```
The Matchmaking UI will instantly be available in your browser at `http://localhost:8501`.

---

## The Workflow

1. **Upload Data**: Drag and drop your Group A and Group B CSV files into the browser.
2. **Identity Mapping**: Tell the system which columns correspond to the participant's Name, ID (Email), and extra Contact Info.
3. **Question Mapping**: All remaining columns are treated as questions. You simply specify if they are a Checkbox or Multiple Choice question, and assign a priority weight.
4. **Execute**: Pick your algorithm and click Generate.
5. **Review & Send**: View the matched table in the browser. You can toggle the detailed view, download the results as a CSV, and preview the actual HTML emails with real data.
6. **Email Configuration**: When you are ready to send emails, click "Configure & Send Emails". A secure popup will ask for your Gmail address and a [Google App Password](https://myaccount.google.com/apppasswords) to safely dispatch the matches!

## Email Configuration Setup

If you want to use the built-in email notifier to send matches to participants the app needs to log into a Gmail account. Google no longer allows simple password logins for scripts, so you must generate an **App Password**.

### Tutorial: How to get an App Password
1. Go to your [Google Account Manage page](https://myaccount.google.com/).
2. On the left navigation panel, click **Security**.
3. Under the "How you sign in to Google" section, ensure **2-Step Verification** is turned ON. (You cannot generate an App Password without this).
4. Click on **2-Step Verification**, scroll to the bottom, and click on **App passwords**.
5. Give it a name (e.g., "Matchmaker") and click **Create**.
6. Google will give you a 16-character password in a yellow box. **Copy this password**.

---

## Customizing Email Templates

If you want to create your own email designs:
1. Navigate to `src/templates/`.
2. Create a new folder for your theme (e.g., `src/templates/my-theme/`).
3. Add a `mentor_template.html` and a `mentee_template.html` inside your new folder.
4. The web app will automatically detect your new theme in the "Template Theme" dropdown during Step 5!

*(You can use placeholders like `{{mentor_name}}`, `{{mentee_name}}`, `{{mentor_contact}}`, and `{{mentee_contact}}` in your HTML to inject dynamic data).*
