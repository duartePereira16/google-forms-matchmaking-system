import os
import sys
import pandas as pd
import questionary
from dotenv import load_dotenv

load_dotenv()
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

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

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner_text = """
██████▄  ██████▄  ███ ██████▄   ▄██████ ███  ███ ██████▄   ▄██████
▄▄▄  ▒▒▒ ▄▄▄  ▒▒▒ ▒▒▒ ▄▄▄  ▒▒▀ ▒▒▒▒     ▒▒▒▄ ▒▒▒ ▄▄▄  ▒▒▒ ▒▒▒  ▀▀▀
██████▀  ████████ ███ ██████▄  ▀██████▄  ▀██████ ███  ███ ███  ▄▄▄
▒▒▒      ▒▒▒  ▒▒▒ ▒▒▒ ▒▒▒  ▒▒▒      ▒▒▒     ▄▒▒▒ ▒▒▒  ▒▒▒ ▒▒▒  ▒▒▒
███      ███  ███ ███ ███  ███ ██████▀  ██████▀  ███  ███  ▀██████                                                   
    """
    panel = Panel(Text(banner_text, style="bold cyan"), title="[bold green]CLI Edition[/bold green]", expand=False)
    console.print(panel)
    console.print("[dim]Welcome to the interactive Matchmaking terminal interface.[/dim]\n")

def confirm_step_action():
    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Continue to Next Step", value='next'),
            questionary.Choice("Go Back to Previous Step", value='back'),
            questionary.Choice("Exit CLI", value='exit')
        ]
    ).ask()
    return action

def run_step_1(state):
    clear_screen()
    print_banner()
    console.print("[bold yellow]--- Step 1: Data Loading ---[/bold yellow]\n")
    
    group_a_label = questionary.text("Enter label for Group A (e.g., Mentor):", default=state.get('group_a_label', 'Mentor')).ask()
    group_b_label = questionary.text("Enter label for Group B (e.g., Mentee):", default=state.get('group_b_label', 'Mentee')).ask()
    if group_a_label is None: return 'exit'

    path_a = questionary.path(f"Path to {group_a_label} CSV file:", default=state.get('path_a', '')).ask()
    path_b = questionary.path(f"Path to {group_b_label} CSV file:", default=state.get('path_b', '')).ask()
    if path_a is None: return 'exit'

    if not os.path.exists(path_a) or not os.path.exists(path_b):
        console.print("[bold red]Error:[/bold red] One or both files do not exist.")
        questionary.press_any_key_to_continue().ask()
        return 'retry'
    
    try:
        df_a = pd.read_csv(path_a)
        df_b = pd.read_csv(path_b)
    except Exception as e:
        console.print(f"[bold red]Error reading CSVs:[/bold red] {e}")
        questionary.press_any_key_to_continue().ask()
        return 'retry'

    if df_a.empty or df_b.empty:
        console.print("[bold red]Error:[/bold red] One or both CSVs are empty.")
        questionary.press_any_key_to_continue().ask()
        return 'retry'
    
    if list(df_a.columns) != list(df_b.columns):
        console.print("[bold red]Error:[/bold red] Column headers in both CSVs must be perfectly identical.")
        questionary.press_any_key_to_continue().ask()
        return 'retry'
        
    console.print(f"\n[bold green]Successfully loaded {len(df_a)} {group_a_label}s and {len(df_b)} {group_b_label}s![/bold green]\n")
    
    state['group_a_label'] = group_a_label
    state['group_b_label'] = group_b_label
    state['path_a'] = path_a
    state['path_b'] = path_b
    state['df_a'] = df_a
    state['df_b'] = df_b
    state['columns'] = list(df_a.columns)
    
    return confirm_step_action()

def run_step_2(state):
    clear_screen()
    print_banner()
    console.print("[bold yellow]--- Step 2: Identity Mapping ---[/bold yellow]\n")
    
    columns = state['columns']
    
    id_col = questionary.select("Select the ID Column (e.g., Email):", choices=columns).ask()
    if id_col is None: return 'exit'
    
    name_col = questionary.select("Select the Name Column:", choices=columns).ask()
    
    contact_cols = questionary.checkbox("Select any additional Contact Info columns (Space to select, Enter to confirm):", choices=columns).ask()

    selected_identity_cols = set([id_col, name_col] + contact_cols)
    question_cols = [c for c in columns if c not in selected_identity_cols]

    if not question_cols:
        console.print("[bold red]No columns left for questions! The matcher requires at least one question column.[/bold red]")
        questionary.press_any_key_to_continue().ask()
        return 'retry'

    state['id_col'] = id_col
    state['name_col'] = name_col
    state['contact_cols'] = contact_cols
    state['question_cols'] = question_cols
    
    # Initialize default config for step 3 if missing
    if 'question_config' not in state:
        state['question_config'] = {q: {'type': 'Checkbox', 'weight': 1.0} for q in question_cols}
    else:
        # Prune old or missing columns
        state['question_config'] = {q: state['question_config'].get(q, {'type': 'Checkbox', 'weight': 1.0}) for q in question_cols}
        
    return confirm_step_action()

def run_step_3(state):
    clear_screen()
    print_banner()
    console.print("[bold yellow]--- Step 3: Question Configuration ---[/bold yellow]\n")
    
    question_cols = state['question_cols']
    config = state['question_config']
    
    g_cb_str = questionary.text("Enter Global Checkbox Weight:", default="1.0").ask()
    if g_cb_str is None: return 'exit'
    g_mc_str = questionary.text("Enter Global Multiple Choice Weight:", default="1.0").ask()
    
    try:
        g_cb = float(g_cb_str)
        g_mc = float(g_mc_str)
    except ValueError:
        console.print("[red]Invalid global weights. Using 1.0 defaults.[/red]")
        g_cb, g_mc = 1.0, 1.0
        
    # Apply global defaults to all automatically
    for q in question_cols:
        if config[q]['type'] == 'Checkbox':
            config[q]['weight'] = g_cb
        elif config[q]['type'] == 'Multiple Choice':
            config[q]['weight'] = g_mc

    while True:
        clear_screen()
        print_banner()
        console.print("[bold yellow]--- Step 3: Question Configuration ---[/bold yellow]\n")
        
        table = Table(title="Current Question Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Question", style="cyan")
        table.add_column("Type")
        table.add_column("Weight", justify="right")
        
        for q in question_cols:
            c = config[q]
            table.add_row(q, c['type'], f"{c['weight']:.1f}" if c['type'] != 'Exclude' else "-")
        console.print(table)
        console.print("\n[dim]Tip: You can manually override specific questions or proceed if everything looks good.[/dim]")
        
        choices = ["Proceed to Next Step", "Go Back to Previous Step", "Exit CLI"] + [questionary.Separator()] + question_cols
        selection = questionary.select("Action:", choices=choices).ask()
        
        if selection == "Proceed to Next Step":
            active = [q for q, c in config.items() if c['type'] != 'Exclude']
            if not active:
                console.print("[bold red]You must include at least one question to run the matcher.[/bold red]")
                questionary.press_any_key_to_continue().ask()
                continue
            return 'next'
        elif selection == "Go Back to Previous Step":
            return 'back'
        elif selection == "Exit CLI" or selection is None:
            return 'exit'
        else:
            # Edit specific question
            q = selection
            q_type = questionary.select(f"Select Type for '{q}':", choices=['Checkbox', 'Multiple Choice', 'Exclude']).ask()
            if q_type == 'Exclude':
                config[q] = {'type': 'Exclude', 'weight': 0.0}
            else:
                default_w = str(g_cb) if q_type == 'Checkbox' else str(g_mc)
                while True:
                    w_str = questionary.text(f"Enter Weight for '{q}':", default=default_w).ask()
                    try:
                        config[q] = {'type': q_type, 'weight': float(w_str)}
                        break
                    except ValueError:
                        console.print("[red]Please enter a valid number.[/red]")

def run_step_4(state):
    clear_screen()
    print_banner()
    console.print("[bold yellow]--- Step 4: Algorithm & Execution ---[/bold yellow]\n")
    
    console.print(
        "[dim]Available Algorithms:\n"
        "- Hungarian: Guarantees the highest possible global score (Fairest).\n"
        "- Iterative Greedy: Assigns highest scoring pair step-by-step.\n"
        "- Greedy: Fast iteration picking best match for each individual.[/dim]\n"
    )
    
    algo = questionary.select("Select the matching algorithm:", choices=list(ALGORITHMS.keys())).ask()
    if algo is None: return 'exit'

    config = state['question_config']
    checkbox_qs = [q for q, cfg in config.items() if cfg['type'] == 'Checkbox']
    mc_qs = [q for q, cfg in config.items() if cfg['type'] == 'Multiple Choice']
    weights = {q: cfg['weight'] for q, cfg in config.items() if cfg['type'] != 'Exclude'}

    match_config = MatchmakingConfig(
        id_column=state['id_col'],
        name_column=state['name_col'],
        contact_info=state['contact_cols'],
        checkbox_questions=checkbox_qs,
        multiple_choice_questions=mc_qs,
        weights=weights,
        algorithm=algo
    )

    with console.status(f"[bold cyan]Running {algo} matcher...[/bold cyan]", spinner="dots"):
        engine = MatchmakingEngine(match_config)
        matches, score_df = engine.run(state['df_a'], state['df_b'])
        
    console.print(f"\n[bold green]Successfully generated {len(matches)} matches![/bold green]")
    
    table = Table(title="Match Results", show_header=True, header_style="bold magenta")
    table.add_column(state['group_a_label'])
    table.add_column(state['group_b_label'])
    table.add_column("Score", justify="right")
    
    for m in matches:
        table.add_row(m.mentor.name, m.mentee.name, f"{m.score:.1f}")

    console.print(table)
    
    res_df = MatchmakingEngine.format_matches_to_dataframe(
        matches,
        group_a_label=state['group_a_label'],
        group_b_label=state['group_b_label'],
        contact_cols=state['contact_cols']
    )
    res_df.to_csv("matches.csv", index=False)
    console.print("[dim]Matches exported to matches.csv[/dim]\n")

    state['matches'] = matches
    return confirm_step_action()

def run_step_5(state):
    clear_screen()
    print_banner()
    console.print("[bold yellow]--- Step 5: Email Notifications ---[/bold yellow]\n")
    
    template_dirs = [d for d in os.listdir("src/templates") if os.path.isdir(os.path.join("src/templates", d))]
    if not template_dirs:
        console.print("[bold red]No template directories found in `src/templates/`.[/bold red]")
        questionary.press_any_key_to_continue().ask()
        return 'back'

    selected_theme = questionary.select("Select Template Theme:", choices=template_dirs).ask()
    if selected_theme is None: return 'exit'
    
    send_mentors = questionary.confirm(f"Send emails to {state['group_a_label']}s?").ask()
    send_mentees = questionary.confirm(f"Send emails to {state['group_b_label']}s?").ask()
    
    if not send_mentors and not send_mentees:
        console.print("[bold blue]No emails to send. Matches are saved in matches.csv.[/bold blue]")
        return 'done'

    console.print("\n[dim]Please provide credentials for the Google Account sending the emails.[/dim]")
    default_email = os.getenv("SENDER_EMAIL", "")
    sender_email = questionary.text("Enter Sender Email Address:", default=default_email).ask()
    sender_password = questionary.password("Enter App Password:").ask()
    if not sender_password:
        sender_password = os.getenv("SENDER_PASSWORD", "")
    
    if not sender_email or not sender_password:
        console.print("[bold red]Credentials missing. Aborting email send.[/bold red]")
        return 'back'

    theme_dir = os.path.join("src/templates", selected_theme)
    mentee_template_path = os.path.join(theme_dir, "mentee_template.html")

    success_count = 0
    error_count = 0
    
    matches = state['matches']
    grouped_by_mentor = group_matches_by_mentor(matches)
    total_emails = (len(grouped_by_mentor) if send_mentors else 0) + (len(matches) if send_mentees else 0)

    try:
        with EmailDispatcher(sender_email, sender_password) as dispatcher:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Sending emails...", total=total_emails)
                
                # 1. Send consolidated emails to mentors using appropriate single or multi template
                if send_mentors:
                    for mentor_id, m_list in grouped_by_mentor.items():
                        mentor = m_list[0].mentor
                        m_ctx = build_mentor_email_context(mentor, m_list, theme_dir=theme_dir)
                        mentor_template_path = resolve_mentor_template_path(theme_dir, len(m_list))
                        if os.path.exists(mentor_template_path):
                            try:
                                html_body = format_template(mentor_template_path, m_ctx)
                                dispatcher.send_email(mentor.id, f"Matchmaking Result - {state['group_a_label']}", html_body)
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                console.print(f"[red]Error sending to {mentor.id}: {e}[/red]")
                        else:
                            error_count += 1
                            console.print(f"[red]Template missing: {mentor_template_path}[/red]")
                        progress.advance(task)
                
                # 2. Send emails to mentees
                if send_mentees and os.path.exists(mentee_template_path):
                    for m in matches:
                        m_ctx = build_mentee_email_context(m)
                        try:
                            html_body = format_template(mentee_template_path, m_ctx)
                            dispatcher.send_email(m.mentee.id, f"Matchmaking Result - {state['group_b_label']}", html_body)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            console.print(f"[red]Error sending to {m.mentee.id}: {e}[/red]")
                        progress.advance(task)
    except Exception as e:
        console.print(f"[bold red]SMTP Connection Error:[/bold red] {e}")

    if error_count == 0:
        console.print(f"\n[bold green]Successfully sent {success_count} emails! All done.[/bold green]")
    else:
        console.print(f"\n[bold yellow]Sent {success_count} emails, but encountered {error_count} errors.[/bold yellow]")

    return 'done'

def main():
    state = {}
    step = 1

    while 1 <= step <= 5:
        if step == 1:
            res = run_step_1(state)
            if res == 'next': step = 2
            elif res == 'exit': break
        elif step == 2:
            res = run_step_2(state)
            if res == 'next': step = 3
            elif res == 'back': step = 1
            elif res == 'exit': break
        elif step == 3:
            res = run_step_3(state)
            if res == 'next': step = 4
            elif res == 'back': step = 2
            elif res == 'exit': break
        elif step == 4:
            res = run_step_4(state)
            if res == 'next': step = 5
            elif res == 'back': step = 3
            elif res == 'exit': break
        elif step == 5:
            res = run_step_5(state)
            if res == 'back': step = 4
            elif res in ['exit', 'done']: break
            
    console.print("\n[bold blue]Exiting Matchmaker CLI. Goodbye![/bold blue]\n")

if __name__ == "__main__":
    main()
