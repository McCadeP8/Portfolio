import pandas as pd
import openpyxl
import numpy as np

def get_picks():
    file_path = "MARCH MADNESS 2021 brackets.xlsm"

    wb = openpyxl.load_workbook(file_path, data_only=True)

    cells = []

    # F and X columns
    for r in [4,8,12,16,20,24,28,32,38,42,46,50,54,58,62,66]:
        cells.append(f"F{r}")
    for r in [4,8,12,16,20,24,28,32,38,42,46,50,54,58,62,66]:
        cells.append(f"V{r}")

    # H and T
    for r in [6,14,22,30,40,48,56,64]:
        cells.append(f"H{r}")
    for r in [6,14,22,30,40,48,56,64]:
        cells.append(f"T{r}")

    # J and R
    for r in [10,26,44,60]:
        cells.append(f"J{r}")
    for r in [10,26,44,60]:
        cells.append(f"R{r}")

    # L and P
    cells += ["L17","L51","P17","P51"]

    # N column
    cells += ["N32","N38","N35"]

    # Final cell
    cells += ["L1"]

    rows = []

    for sheet in wb.sheetnames:
        ws = wb[sheet]
        values = [ws[cell].value for cell in cells]
        rows.append([sheet] + values)

    result = pd.DataFrame(rows, columns=["SheetName"] + cells)

    result = result[(result["N35"].notna()) & (result["N35"] != 54)]

    result = result.drop(columns=["SheetName"])

    result = result.rename(columns={
        "F4": "R64_1",
        "F8": "R64_2",
        "F12": "R64_3",
        "F16": "R64_4",
        "F20": "R64_5",
        "F24": "R64_6",
        "F28": "R64_7",
        "F32": "R64_8",
        "F38": "R64_9",
        "F42": "R64_10",
        "F46": "R64_11",
        "F50": "R64_12",
        "F54": "R64_13",
        "F58": "R64_14",
        "F62": "R64_15",
        "F66": "R64_16",
        "V4": "R64_17",
        "V8": "R64_18",
        "V12": "R64_19",
        "V16": "R64_20",
        "V20": "R64_21",
        "V24": "R64_22",
        "V28": "R64_23",
        "V32": "R64_24",
        "V38": "R64_25",
        "V42": "R64_26",
        "V46": "R64_27",
        "V50": "R64_28",
        "V54": "R64_29",
        "V58": "R64_30",
        "V62": "R64_31",
        "V66": "R64_32",
        "H6": "R32_1",
        "H14": "R32_2",
        "H22": "R32_3",
        "H30": "R32_4",
        "H40": "R32_5",
        "H48": "R32_6",
        "H56": "R32_7",
        "H64": "R32_8",
        "T6": "R32_9",
        "T14": "R32_10",
        "T22": "R32_11",
        "T30": "R32_12",
        "T40": "R32_13",
        "T48": "R32_14",
        "T56": "R32_15",
        "T64": "R32_16",
        "J10": "S16_1",
        "J26": "S16_2",
        "J44": "S16_3",
        "J60": "S16_4",
        "R10": "S16_5",
        "R26": "S16_6",
        "R44": "S16_7",
        "R60": "S16_8",
        "L17": "E8_1",
        "L51": "E8_2",
        "P17": "E8_3",
        "P51": "E8_4",
        "N32": "F4_1",
        "N38": "F4_2",
        "N35": "Champ",
        "L1": "Bracket"
        })

    return result

def get_projections():
    csv_url = "https://docs.google.com/spreadsheets/d/12f4bu9JRwZ9TDXVw6T2GI0fPgjeKCk1GxrdDFdjHds8/export?format=csv&gid=1837691522"
    df = pd.read_csv(csv_url)
    return df

def calculate_expected_points():

    round_points = {
        'R64':   1,
        'R32':   3,
        'S16':   6,
        'E8':    12,
        'F4':    24,
        'Champ': 32
    }

    round_prob_col = {
        'R64':   'R32',
        'R32':   'S16',
        'S16':   'E8',
        'E8':    'F4',
        'F4':    'Champ',
        'Champ': 'Champ'
    }

    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']
    }

    team_info = projections.set_index('Team')

    results = []

    for _, row in picks.iterrows():
        row_exp = {}

        for round_name, cols in round_cols.items():
            base_pts  = round_points[round_name]
            prob_col  = round_prob_col[round_name]
            round_exp = 0.0

            for col in cols:
                team = row[col]
                if pd.isna(team) or team not in team_info.index:
                    continue
                seed = team_info.loc[team, 'Seed']
                prob = team_info.loc[team, prob_col]  # ← removed / 100
                round_exp += prob * (base_pts + seed)

            row_exp[round_name] = round_exp

        row_exp['Total'] = sum(row_exp.values())
        results.append(row_exp)

    expected_df = pd.DataFrame(results, columns=['R64', 'R32', 'S16', 'E8', 'F4', 'Champ', 'Total'])

    return expected_df

def calculate_risk_score():

    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12, 'F4': 24, 'Champ': 32}

    round_prob_col = {
        'R64': 'R32', 'R32': 'S16', 'S16': 'E8',
        'E8': 'F4', 'F4': 'Champ', 'Champ': 'Champ'
    }

    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']
    }

    team_info = projections.set_index('Team')
    results = []

    for _, row in picks.iterrows():
        downside      = 0.0
        total_exp     = 0.0
        champ_exp     = 0.0
        upset_num     = 0.0
        upset_denom   = 0.0

        for round_name, cols in round_cols.items():
            base_pts = round_points[round_name]
            prob_col = round_prob_col[round_name]

            for col in cols:
                team = row[col]
                if pd.isna(team) or team not in team_info.index:
                    continue

                seed     = team_info.loc[team, 'Seed']
                prob     = team_info.loc[team, prob_col]
                pts      = base_pts + seed
                exp_pts  = prob * pts

                # Component 1: Downside exposure
                downside += (1 - prob) * pts

                # Component 2: Track champ + total expected pts
                total_exp += exp_pts
                if round_name == 'Champ':
                    champ_exp = exp_pts

                # Component 3: Upset tendency — seed weighted by round multiplier
                upset_num   += seed * base_pts
                upset_denom += base_pts

        champ_concentration = (champ_exp / total_exp * 100) if total_exp > 0 else 0
        avg_upset_seed      = (upset_num / upset_denom) if upset_denom > 0 else 0

        results.append({
            'downside':            downside,
            'champ_concentration': champ_concentration,
            'avg_upset_seed':      avg_upset_seed
        })

    df = pd.DataFrame(results)

    # Normalize each component to 0–100
    def normalize(col):
        mn, mx = col.min(), col.max()
        return (col - mn) / (mx - mn) * 100 if mx > mn else col * 0

    df['downside_score']       = normalize(df['downside'])
    df['concentration_score']  = normalize(df['champ_concentration'])
    df['upset_score']          = normalize(df['avg_upset_seed'])

    # Weighted composite — downside matters most
    df['risk_score'] = (
        df['downside_score']      * 0.50 +
        df['concentration_score'] * 0.25 +
        df['upset_score']         * 0.25
    )

    # Add bracket name and rank
    df['Bracket']   = picks['Bracket'].values
    df['risk_rank'] = df['risk_score'].rank(ascending=False).astype(int)

    return df[['Bracket', 'risk_score', 'risk_rank',
               'downside_score', 'concentration_score', 'upset_score']].sort_values('risk_rank')

def run_simulations(projections, n_simulations=10000):
    next_round_prob = {
        'R64': 'R32', 'R32': 'S16', 'S16': 'E8',
        'E8': 'F4', 'F4': 'Champ', 'Champ': 'Champ'
    }
    round_slots = {
        'R64':   [f'R64_{i}'   for i in range(1, 33)],
        'R32':   [f'R32_{i}'   for i in range(1, 17)],
        'S16':   [f'S16_{i}'   for i in range(1, 9)],
        'E8':    [f'E8_{i}'    for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']
    }
    team_info = projections.set_index('Team')

    def simulate_one():
        current_teams = projections['Team'].values.tolist()
        row = {}
        for round_name, slots in round_slots.items():
            winners = []
            for i in range(len(current_teams) // 2):
                team_a = current_teams[i * 2]
                team_b = current_teams[i * 2 + 1]
                # Always use Champ prob as the strength signal — avoids
                # the cumulative-probability mismatch in later rounds
                pa = team_info.loc[team_a, 'Champ']
                pb = team_info.loc[team_b, 'Champ']
                total = pa + pb
                p_a = pa / total if total > 0 else 0.5
                winners.append(team_a if np.random.random() < p_a else team_b)
            for slot, winner in zip(slots, winners):
                row[slot] = winner
            current_teams = winners
        return row

    rows = []
    for sim in range(n_simulations):
        if sim % 1000 == 0:
            print(f"  Simulation {sim}/{n_simulations}...")
        rows.append(simulate_one())

    return pd.DataFrame(rows)

def score_simulations(picks, simulations, projections):
    """
    Scores every bracket against every simulated tournament.
    Returns a dataframe of shape (n_simulations, 136)
    Columns = bracket names, rows = simulations
    """
    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12, 'F4': 24, 'Champ': 32}
    round_cols   = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']
    }
    team_info = projections.set_index('Team')

    all_cols = [col for cols in round_cols.values() for col in cols]
    scores   = np.zeros((len(simulations), len(picks)))

    for sim_idx, sim_row in simulations.iterrows():
        if sim_idx % 1000 == 0:
            print(f"  Scoring simulation {sim_idx}/{len(simulations)}...")

        sim_winners = {
            round_name: set(sim_row[cols].values)
            for round_name, cols in round_cols.items()
        }

        for bracket_idx, (_, picks_row) in enumerate(picks.iterrows()):
            total = 0
            for round_name, cols in round_cols.items():
                base_pts = round_points[round_name]
                for col in cols:
                    team = picks_row[col]
                    if pd.isna(team) or team not in team_info.index:
                        continue
                    if team in sim_winners[round_name]:
                        total += base_pts + team_info.loc[team, 'Seed']
            scores[sim_idx, bracket_idx] = total

    return pd.DataFrame(scores, columns=picks['Bracket'].values)


def calculate_finish_chances(scores_df, top_n=20):
    """
    Takes scores dataframe (n_simulations x 136) and returns
    p_first and p_top_n for each bracket.
    """
    n_simulations = len(scores_df)
    ranks_matrix  = scores_df.rank(axis=1, ascending=False, method='min').values

    return pd.DataFrame({
        'Bracket': scores_df.columns,
        'p_first': ((ranks_matrix == 1).sum(axis=0)    / n_simulations * 100).round(2),
        f'p_top{top_n}': ((ranks_matrix <= top_n).sum(axis=0) / n_simulations * 100).round(2),
    }).sort_values('p_first', ascending=False).reset_index(drop=True)