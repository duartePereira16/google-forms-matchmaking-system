# Google Forms Matchmaking System 🧩

This project automates the process of matching two groups of people based on their answers to Google Forms. It is designed to maximize compatibility between members of the two groups while ensuring fairness in assignments.

Recently refactored into a robust Python package, it now features a modular "Hybrid" architecture, multiple matching strategies (Greedy, Hungarian), and Docker support for easy deployment.

---

## Features

- **Flexible Matching**: Works for any two groups (e.g., mentors and mentees, teammates, dates).
- **Multiple Algorithms**: Choose between **Global Greedy**, **Iterative Greedy** (Legacy), or **Hungarian** (Optimal) strategies.
- **Customizable Scoring**: Define questions and weights in `config.json` without touching code.
- **Scalable Architecture**: Built with a "Functional Core, Modular Shell" design to handle large datasets.
- **Dockerized**: Run anywhere without dependency headaches.

---

## Use Case: Freshman–Veteran Matching 🎓

One example use case is matching **freshmen** with **veterans** to help integrate new students into academic life. Veterans can contact their assigned freshmen to offer guidance and support.

*Note: While built for this context, the system is agnostic and can match any Group A to Group B.*

---

## How It Works

1. **Data Input**
   - Two groups (e.g., Group A and Group B) fill out Google Forms.
   - Export responses as CSV files and place them in `data/inputs/`.
   - Configure file paths and column names in `config/config.json`.

2. **Compatibility Scoring (Functional Core)**
   - **Checkbox questions**: Computes intersection of interests (weighted).
   - **Multiple-choice questions**: Exact matches earn points (weighted).
   - Logic is handled by pure functions in `src/scorer.py`.

3. **Assignment Logic (Strategy Pattern)**
   - **Greedy**: Sorts *all* potential matches by score and picks the best global pairs.
   - **Iterative Greedy**: The original logic—iterates through freshmen one by one.
   - **Hungarian**: Uses the Kuhn-Munkres algorithm for mathematically optimal assignments.

4. **Output Files**
   - Final matches saved to `data/outputs/matches.csv`.
   - Compatibility score matrix saved for analysis.

---

## Setup & Running

1. Clone this repository:
```bash
   git clone [https://github.com/your-username/google-forms-matchmaker.git](https://github.com/your-username/google-forms-matchmaker.git)
   cd google-forms-matchmaker

```

2. Configure the project:
* Edit `config/config.json` to specify your input files, questions, and weights.


3. Run the application:
**Option A: Using Docker (Recommended)**
```bash
# Build the image
docker build -t matchmaker .

# Run with data volume mount
docker run --rm -v $(pwd)/data:/app/data matchmaker

```


**Option B: Local Python**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python -m src.main --config config/config.json

```


4. Check the output files:
* `data/outputs/matches.csv`



---

## Example Configuration

Here’s an example `config.json` for freshman-veteran matching:

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
            "Preferred Day",
            "Favorite Philosopher"
        ]
    },
    "scoring": {
        "checkbox_weight": 1.0,
        "multiple_choice_weight": 2.0
    },
    "algorithm": "iterative_greedy"
}

```

---

## Limitations & Future Improvements

* **Tie-Breaking**: The `iterative_greedy` algorithm relies on CSV order for ties. (Fix: Use `greedy` or `hungarian` for order-independent results).
* **Capacity Handling**: Currently assumes static capacity or simple distribution logic.

**Future Improvements**:

* Build a web interface for easier use.
* Add negative scoring (penalties) for incompatible answers.
* Implement a Genetic Algorithm for multi-objective optimization.

---
