import argparse
import pandas as pd
import json
from src.loader import load_participants
from src.scorer import compute_match_score
from src.strategies import ALGORITHMS

def save_matches(matches, output_path, config_cols, labels):
    """
    Saves matches using dynamic labels defined in config.
    """
    # 1. Get labels from config (Defaults to "Group A" and "Group B")
    label_a = labels.get("group_a", "Group A")
    label_b = labels.get("group_b", "Group B")

    output_data = []
    contact_fields = config_cols.get('contact_info', [])

    for match in matches:
        # 2. Use the dynamic labels for keys
        row = {
            f"{label_b} Name": match.mentee.name,
            f"{label_a} Name": match.mentor.name,
            "Score": match.score
        }
        
        # 3. Add dynamic contact info
        for field in contact_fields:
            row[f"{label_b} {field}"] = match.mentee.attributes.get(field, "N/A")
            row[f"{label_a} {field}"] = match.mentor.attributes.get(field, "N/A")
            
        output_data.append(row)

    if output_data:
        pd.DataFrame(output_data).to_csv(output_path, index=False)
        print(f"Saved matches to {output_path} (Labels: {label_a} & {label_b})")
    else:
        print("No matches found to save.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/mockConfig.json")
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as f:
        config = json.load(f)

    # --- Load Data ---
    print("Loading Group B...")
    group_b = load_participants(
        config['files']['group_b'], 
        config['columns'], 
        is_mentor=False
    )

    print(f"Loading Group A... (Allocating capacity for {len(group_b)} items)")
    group_a = load_participants(
        config['files']['group_a'], 
        config['columns'], 
        is_mentor=True, 
        mentee_count=len(group_b)
    )

    # --- Score ---
    print("Computing scores...")
    score_data = {}
    for b in group_b:
        col_scores = []
        for a in group_a:
            s = compute_match_score(a, b, config['scoring'])
            col_scores.append(s)
        score_data[b.id] = col_scores
    
    score_df = pd.DataFrame(score_data, index=[a.id for a in group_a])

    # --- Match ---
    algo_name = config.get("algorithm", "greedy")
    MatcherClass = ALGORITHMS.get(algo_name)
    if not MatcherClass:
        raise ValueError(f"Unknown algorithm: {algo_name}")
        
    print(f"Running {algo_name}...")
    matcher = MatcherClass()
    results = matcher.match(group_a, group_b, score_df)

    # --- Save (Passing the labels) ---
    # We pass the 'labels' dictionary from config to the save function
    group_labels = config.get('labels', {})
    save_matches(results, config['files']['output'], config['columns'], group_labels)

if __name__ == "__main__":
    main()