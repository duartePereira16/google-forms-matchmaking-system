
---

# Freshmen–Veteran Matching System 🎓

This project automates the process of matching **freshmen** with **veterans** based on answers from Google Forms.
It ensures every freshman is assigned a veteran, while trying to maximize compatibility and keep assignments fair.

---

## How it Works

1. **Data Input**

   * Freshmen and veterans fill out Google Forms with multiple-choice and checkbox-style questions.
   * Export responses as CSV files:

     * `FCT Unio - Caloiros (Respostas).csv`
     * `FCT Unio - Veteranos (Respostas).csv`

2. **Compatibility Scoring**

   * **Checkbox questions** → +1 point for every common option between freshman and veteran.
   * **Multiple-choice questions** → +1 point if both picked the same option.
   * The final score is the sum of these points.

3. **Assignment Logic**

   * If **freshmen ≥ veterans** → Each veteran gets a balanced number of freshmen.
   * If **freshmen < veterans** → Each veteran can take at most 1 freshman.
   * Freshmen are assigned to the **best available veteran match** under these rules.
   * This ensures **no freshman is left without a veteran**.

---

## Output Files

The program generates two CSV files:

* **`compatibility_scores.csv`**
  A matrix with freshmen as columns, veterans as rows, and the compatibility score in each intersection.
  Can be useful for a manual analysis.

* **`matches.csv`**
  Final pairings with:

  * Freshman + Veteran names
  * Emails and phone numbers (from the forms)
  * Compatibility score

---

## Setup & Running

1. Clone this repository:

   ```bash
   git clone https://github.com/duartePereira16/veteran-freshman-matcher.git
   cd veteran-freshman-matcher
   ```

2. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install pandas
   ```

4. Place your CSV files (`FCT Unio - Caloiros (Respostas).csv` and `FCT Unio - Veteranos (Respostas).csv`) in the project folder.

5. Run the script:

   ```bash
   python matchmaking.py
   ```

6. Check the generated output files:

   * `matches.csv`
   * `compatibility_scores.csv`

---

## Limitations & Future Improvements

* The assignment algorithm is **greedy** → it looks for the best match freshman by freshman, not the best global assignment.
* Veterans may still remain unmatched if there are fewer freshmen than veterans.
* Tie-breaking depends on CSV order when multiple veterans have the same score.

**Potential improvements:**

* Implement a better matching algorithm to achieve global optimization.
* Add more sophisticated scoring (e.g., weighted questions).
* Create a simple UI or Google Sheets integration for easier use.

---
