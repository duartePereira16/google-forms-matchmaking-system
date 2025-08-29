import pandas as pd


CHECK_BOX_QUESTIONS = [
    "O que gostas de fazer no teu tempo livre?",
    "Género de música preferido",
    "Ananás na pizza",
    "Um mendigo aproxima-se e tenta roubar o salame que tens dentro da mochila. O que farias nesta situação?",
    "Equipa de futebol preferida"
]

MULTIPLE_CHOICE_QUESTIONS = [
    "Melhor dia para fazer sexo",
    "Filósofo Favorito"
]



def compute_compatibility(freshman, veteran):

    # goes through the checkbox questions. convert the answers to sets and compute the intersection. one point per common answer ig
    # go through the multiple choice questions. one point per common answer ig

    score = 0

    for question in CHECK_BOX_QUESTIONS:
        freshman_answers = set(map(str.strip, freshman[question].split(',')))   # convert to set and strip whitespace
        veteran_answers = set(map(str.strip, veteran[question].split(',')))     # convert to set and strip whitespace
        score += len(freshman_answers & veteran_answers)                        # intersection and count common answers

    for question in MULTIPLE_CHOICE_QUESTIONS:
        if freshman[question] == veteran[question]:
            score += 1

    return score

def main():

    freshmen = pd.read_csv('FCT Unio - Caloiros (Respostas).csv')
    veterans = pd.read_csv('FCT Unio - Veteranos (Respostas).csv')

    nr_freshman = len(freshmen)
    nr_veterans = len(veterans)
    veteran_capacities = {}

    if nr_freshman < nr_veterans:
        for i, (_, veteran) in enumerate(veterans.iterrows()):
            veteran_capacities[veteran["Nome Completo"]] = 1
    else:
        base_capacity = nr_freshman // nr_veterans
        remainder = nr_freshman % nr_veterans

        for i, (_, veteran) in enumerate(veterans.iterrows()):
            if i < remainder:
                veteran_capacities[veteran["Nome Completo"]] = base_capacity + 1
            else:
                veteran_capacities[veteran["Nome Completo"]] = base_capacity

    # this will have data in the form of {"Freshman": freshman["Name"], Veteran": best_veteran,"Score": score} and will include emails and phone nr
    matches = [] 

    # this to create a dataframe with veterans as rows and freshman as columns and the scores as values and store in csv just for analysis
    compatibility_data = []

    # load balancer dictionary (to track how many freshmen each veteran has been matched with)
    veteran_match_count = {veteran["Nome Completo"]: 0 for _, veteran in veterans.iterrows()}

    for _, freshman in freshmen.iterrows():
        best_match = None
        best_score = 0

        for _, veteran in veterans.iterrows():

            score = compute_compatibility(freshman, veteran)

            compatibility_data.append({
                "Freshman": freshman["Nome Completo"],
                "Veteran": veteran["Nome Completo"],
                "Score": score
            })

            if score > best_score and veteran_match_count[veteran["Nome Completo"]] < veteran_capacities[veteran["Nome Completo"]]:
                best_score = score
                best_match = veteran

        if best_match is not None:
            matches.append(
                {"Freshman": freshman["Nome Completo"],
                 "Freshman Email": freshman["Endereço de email"],
                 "Freshman Phone": freshman["Número de Telemóvel"],
                 "Veteran": best_match["Nome Completo"],
                 "Veteran Email": best_match["Endereço de email"],
                 "Veteran Phone": best_match["Número de Telemóvel"],
                 "Score": best_score}
                )
            veteran_match_count[best_match["Nome Completo"]] += 1

    # Save compatibility data to CSV for manual analysis
    compatibility_df = pd.DataFrame(compatibility_data)
    compatibility_matrix = compatibility_df.pivot(index='Veteran', columns='Freshman', values='Score').fillna(0)
    compatibility_matrix.to_csv('compatibility_scores.csv')
    print("Compatibility scores saved to compatibility_scores.csv")

    # Save matches to CSV
    matches_df = pd.DataFrame(matches)
    matches_df.to_csv('matches.csv', index=False)
    print("Matches saved to matches.csv")

    


if __name__ == "__main__":
    main()