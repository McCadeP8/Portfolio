import pandas as pd
import openpyxl
import numpy as np
import plotly.graph_objects as go
import streamlit as st

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_picks():
    file_path = os.path.join(BASE_DIR, "MARCH MADNESS 2021 brackets.xlsm")
    
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

def calculate_expected_points(projections, picks):

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

def calculate_risk_score(projections, picks):

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
                downside += (1 - prob) * pts
                total_exp += exp_pts
                if round_name == 'Champ':
                    champ_exp = exp_pts
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
    def normalize(col):
        mn, mx = col.min(), col.max()
        return (col - mn) / (mx - mn) * 100 if mx > mn else col * 0

    df['downside_score']       = normalize(df['downside'])
    df['concentration_score']  = normalize(df['champ_concentration'])
    df['upset_score']          = normalize(df['avg_upset_seed'])
    df['risk_score'] = (
        df['downside_score']      * 0.50 +
        df['concentration_score'] * 0.25 +
        df['upset_score']         * 0.25
    )
    df['Bracket']   = picks['Bracket'].values
    df['risk_rank'] = df['risk_score'].rank(ascending=False).astype(int)

    return df[['Bracket', 'risk_score', 'risk_rank',
               'downside_score', 'concentration_score', 'upset_score']].sort_values('risk_rank')

@st.cache_data
def run_simulations(projections, n_simulations=100000):
    teams = projections['Team'].values
    group_map = projections.set_index('Team')
    def draw_round(prob_col, group_col, n_groups):
        draws = {}
        for g in range(1, n_groups + 1):
            g_teams = projections[projections[group_col] == g]
            probs = g_teams[prob_col].values / g_teams[prob_col].sum()
            draws[g] = np.random.choice(g_teams['Team'].values, size=n_simulations, p=probs)
        return draws
    champ_probs = projections['Champ'].values / projections['Champ'].sum()
    champions = np.random.choice(teams, size=n_simulations, p=champ_probs)
    f4  = draw_round('F4',  'F4Group',  2)
    e8  = draw_round('E8',  'E8Group',  4)
    s16 = draw_round('S16', 'S16Group', 8)
    r32 = draw_round('R32', 'R32Group', 16)
    r64 = draw_round('R64', 'R64Group', 32)
    champ_f4 = group_map.loc[champions, 'F4Group'].values
    for g in [1, 2]:
        f4[g] = np.where(champ_f4 == g, champions, f4[g])
    for g in [1, 2]:
        winner_e8 = group_map.loc[f4[g], 'E8Group'].values
        for eg in [2*g-1, 2*g]:
            e8[eg] = np.where(winner_e8 == eg, f4[g], e8[eg])
    for g in range(1, 5):
        winner_s16 = group_map.loc[e8[g], 'S16Group'].values
        for sg in [2*g-1, 2*g]:
            s16[sg] = np.where(winner_s16 == sg, e8[g], s16[sg])
    for g in range(1, 9):
        winner_r32 = group_map.loc[s16[g], 'R32Group'].values
        for rg in [2*g-1, 2*g]:
            r32[rg] = np.where(winner_r32 == rg, s16[g], r32[rg])
    for g in range(1, 17):
        winner_r64 = group_map.loc[r32[g], 'R64Group'].values
        for rg in [2*g-1, 2*g]:
            r64[rg] = np.where(winner_r64 == rg, r32[g], r64[rg])
    results = pd.DataFrame({'Sim': range(1, n_simulations + 1), 'Champ': champions})
    for g in [1, 2]:          
        results[f'F4_{g}']  = f4[g]
    for g in range(1, 5):   
        results[f'E8_{g}']  = e8[g]
    for g in range(1, 9):     
        results[f'S16_{g}'] = s16[g]
    for g in range(1, 17):    
        results[f'R32_{g}'] = r32[g]
    for g in range(1, 33):    
        results[f'R64_{g}'] = r64[g]
    for i in range(0, n_simulations, 10000):
        print(f"  Simulations {i+1}-{min(i+10000, n_simulations)} complete...")
    print(f"  All {n_simulations} simulations complete.")

    return results

@st.cache_data
def score_simulations(picks, simulations, projections):
    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12, 'F4': 24, 'Champ': 32}
    round_cols   = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']
    }
    seed_map = projections.set_index('Team')['Seed']
    all_cols = [col for cols in round_cols.values() for col in cols]
    slot_points = {col: round_points[rnd] for rnd, cols in round_cols.items() for col in cols}
    sim_arr   = simulations[all_cols].values
    picks_arr = picks[all_cols].values
    pick_points = np.array([
        [slot_points[col] + seed_map.get(picks_arr[b, j], 0)
         for j, col in enumerate(all_cols)]
        for b in range(len(picks))
    ], dtype=np.float32)
    scores = np.zeros((len(simulations), len(picks)), dtype=np.float32)
    for j in range(len(all_cols)):
        match = sim_arr[:, j, None] == picks_arr[None, :, j]  # (n_sims, n_brackets)
        scores += match * pick_points[None, :, j]
    for i in range(0, len(simulations), 1000):
        print(f"  Scored simulations {i+1}-{min(i+1000, len(simulations))}...")
    print(f"  All {len(simulations)} simulations scored.")
    return pd.DataFrame(scores, columns=picks['Bracket'].values)

@st.cache_data
def calculate_finish_chances(scores_df):
    n_simulations = len(scores_df)
    ranks_matrix  = scores_df.rank(axis=1, ascending=False, method='min').values.astype(int)
    brackets = scores_df.columns
    finish_matrix = np.zeros((len(brackets), 30), dtype=np.float32)
    for place in range(1, 31):
        finish_matrix[:, place - 1] = (ranks_matrix == place).sum(axis=0) / n_simulations * 100
    result = pd.DataFrame(
        finish_matrix,
        index=brackets,
        columns=[f'P{place}' for place in range(1, 31)]
    ).round(2)
    result.index.name = 'Bracket'
    return result.sort_values('P1', ascending=False).reset_index()

@st.cache_data
def compute_all_results(picks, simulations):
    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ'],
    }
    all_cols = [col for cols in round_cols.values() for col in cols]
    sim_matrix = simulations[all_cols].values

    records = []
    for _, row in picks.iterrows():
        bracket = row['Bracket']
        entry = {'Bracket': bracket}
        total_correct = np.zeros(len(simulations), dtype=int)

        for round_name, cols in round_cols.items():
            col_indices = [all_cols.index(c) for c in cols]
            bracket_picks = row[cols].values
            sim_slice = sim_matrix[:, col_indices]
            correct_per_sim = (sim_slice == bracket_picks).sum(axis=1)
            total_correct += correct_per_sim

            max_correct = len(cols)
            counts = np.bincount(correct_per_sim, minlength=max_correct + 1)[:max_correct + 1]
            entry[f'{round_name}_counts'] = counts
            entry[f'{round_name}_mean'] = correct_per_sim.mean()

        # Compute All directly from simulation totals
        counts_all = np.bincount(total_correct, minlength=64)[:64]
        entry['All_counts'] = counts_all
        entry['All_mean'] = total_correct.mean()

        records.append(entry)
    return pd.DataFrame(records)

def plot_correct_picks(results_df, selected_bracket, round_name='R64'):
    round_max = {
        'R64': 32, 'R32': 16, 'S16': 8, 'E8': 4, 'F4': 2, 'Champ': 1, 'All': 63
    }

    row = results_df[results_df['Bracket'] == selected_bracket].iloc[0]

    if round_name == 'All':
        counts = row['All_counts']
        mean_val = row['All_mean']
    else:
        counts = row[f'{round_name}_counts']
        mean_val = row[f'{round_name}_mean']

    max_correct = round_max[round_name]
    x = list(range(len(counts)))
    pct = counts / counts.sum() * 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x,
        y=pct,
        marker_color='#009CDE',
        marker_line_width=0,
    ))

    fig.add_vline(
        x=mean_val,
        line_dash='dash',
        line_color='red',
        line_width=1.5
    )

    fig.update_layout(
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font_color='white',
        xaxis=dict(
            title='Number of Correct Picks',
            range=[-0.5, max_correct + 0.5],
            tickfont=dict(color='white'),
            gridcolor='#444444',
        ),
        yaxis=dict(
            title='Probability (%)',
            ticksuffix='%',
            tickfont=dict(color='white'),
            gridcolor='#444444',
        ),
        bargap=0,
        showlegend=False,
        margin=dict(l=50, r=20, t=20, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def compute_all_results_p(picks, simulations):
    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ'],
    }
    round_points = {
        'R64':   1,
        'R32':   2,
        'S16':   4,
        'E8':    8,
        'F4':    16,
        'Champ': 32,
    }
    all_cols = [col for cols in round_cols.values() for col in cols]
    sim_matrix = simulations[all_cols].values

    records = []
    for _, row in picks.iterrows():
        bracket = row['Bracket']
        entry = {'Bracket': bracket}
        total_points = np.zeros(len(simulations), dtype=int)

        for round_name, cols in round_cols.items():
            pts = round_points[round_name]
            col_indices = [all_cols.index(c) for c in cols]
            bracket_picks = row[cols].values
            sim_slice = sim_matrix[:, col_indices]
            points_per_sim = (sim_slice == bracket_picks).sum(axis=1) * pts
            total_points += points_per_sim

            max_points = len(cols) * pts
            counts = np.bincount(points_per_sim, minlength=max_points + 1)[:max_points + 1]
            entry[f'{round_name}_counts'] = counts
            entry[f'{round_name}_mean'] = points_per_sim.mean()

        max_total = sum(len(cols) * round_points[r] for r, cols in round_cols.items())  # 192
        counts_all = np.bincount(total_points, minlength=max_total + 1)[:max_total + 1]
        entry['All_counts'] = counts_all
        entry['All_mean'] = total_points.mean()

        records.append(entry)
    return pd.DataFrame(records)


def plot_correct_picks_p(results_df, selected_bracket, round_name='R64'):
    round_max = {
        'R64': 32, 'R32': 16, 'S16': 8, 'E8': 4, 'F4': 2, 'Champ': 1, 'All': 63
    }

    row = results_df[results_df['Bracket'] == selected_bracket].iloc[0]

    if round_name == 'All':
        counts = row['All_counts']
        mean_val = row['All_mean']
    else:
        counts = row[f'{round_name}_counts']
        mean_val = row[f'{round_name}_mean']

    max_correct = round_max[round_name]
    x = list(range(len(counts)))
    pct = counts / counts.sum() * 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x,
        y=pct,
        marker_color='#009CDE',
        marker_line_width=0,
    ))

    fig.add_vline(
        x=mean_val,
        line_dash='dash',
        line_color='red',
        line_width=1.5
    )

    fig.update_layout(
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font_color='white',
        xaxis=dict(
            title='Number of Correct Picks',
            range=[-0.5, max_correct + 0.5],
            tickfont=dict(color='white'),
            gridcolor='#444444',
        ),
        yaxis=dict(
            title='Probability (%)',
            ticksuffix='%',
            tickfont=dict(color='white'),
            gridcolor='#444444',
        ),
        bargap=0,
        showlegend=False,
        margin=dict(l=50, r=20, t=20, b=50),
    )

    st.plotly_chart(fig, use_container_width=True, key=f"correct_{selected_bracket}_{round_name}")

# F