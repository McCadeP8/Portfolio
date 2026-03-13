import pandas as pd
import openpyxl
import numpy as np
import streamlit.components.v1 as components
import plotly.graph_objects as go
from functools import reduce
import streamlit as st

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def get_picks():
    file_path = os.path.join(BASE_DIR, "MARCH MADNESS 2021 brackets.xlsm")
    #file_path = ("MARCH MADNESS 2021 brackets.xlsm")
    wb = openpyxl.load_workbook(file_path, data_only=True)
    cells = []
    for r in [4,8,12,16,20,24,28,32,38,42,46,50,54,58,62,66]:
        cells.append(f"F{r}")
    for r in [4,8,12,16,20,24,28,32,38,42,46,50,54,58,62,66]:
        cells.append(f"V{r}")
    for r in [6,14,22,30,40,48,56,64]:
        cells.append(f"H{r}")
    for r in [6,14,22,30,40,48,56,64]:
        cells.append(f"T{r}")
    for r in [10,26,44,60]:
        cells.append(f"J{r}")
    for r in [10,26,44,60]:
        cells.append(f"R{r}")
    cells += ["L17","L51","P17","P51"]
    cells += ["N32","N38","N35"]
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
        "L1": "Bracket"})
    return result

@st.cache_data
def get_projections():
    csv_url = "https://docs.google.com/spreadsheets/d/12f4bu9JRwZ9TDXVw6T2GI0fPgjeKCk1GxrdDFdjHds8/export?format=csv&gid=1837691522"
    df = pd.read_csv(csv_url)
    return df

def calculate_risk_score(projections, picks):
    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12, 'F4': 24, 'Champ': 32}
    round_prob_col = {'R64': 'R32', 'R32': 'S16', 'S16': 'E8', 'E8': 'F4', 'F4': 'Champ', 'Champ': 'Champ'}
    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']}
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
            'avg_upset_seed':      avg_upset_seed})
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
        df['upset_score']         * 0.25)
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
def score_simulations_by_round(picks, simulations, projections):
    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12, 'F4': 24, 'Champ': 32}
    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']}
    seed_map = projections.set_index("Team")["Seed"]
    results = {}
    total_scores = None
    for rnd, cols in round_cols.items():
        sim_arr   = simulations[cols].values
        picks_arr = picks[cols].values
        seed_values = np.vectorize(lambda x: seed_map.get(x, 0))(picks_arr)
        pick_points = seed_values + round_points[rnd]
        match = sim_arr[:, None, :] == picks_arr[None, :, :]        
        scores = (match * pick_points[None, :, :]).sum(axis=2)        
        df = pd.DataFrame(scores, columns=picks["Bracket"].values)
        results[rnd] = df
        if total_scores is None:
            total_scores = scores.copy()        
        else:
            total_scores += scores

    total_df = pd.DataFrame(total_scores, columns=picks["Bracket"].values)
    total_df.insert(0, "Sim", np.arange(1, len(total_df) + 1))
    results["Total"] = total_df

    return (results["R64"], results["R32"], results["S16"], results["E8"], results["F4"], results["Champ"], results["Total"])

@st.cache_data
def count_simulations_by_round(picks, simulations):
    round_cols = {
        'R64':   [f'R64_{i}' for i in range(1, 33)],
        'R32':   [f'R32_{i}' for i in range(1, 17)],
        'S16':   [f'S16_{i}' for i in range(1, 9)],
        'E8':    [f'E8_{i}'  for i in range(1, 5)],
        'F4':    ['F4_1', 'F4_2'],
        'Champ': ['Champ']}
    results = {}
    total_counts = None
    for rnd, cols in round_cols.items():
        sim_arr   = simulations[cols].values
        picks_arr = picks[cols].values
        match = sim_arr[:, None, :] == picks_arr[None, :, :]
        counts = match.sum(axis=2)
        df = pd.DataFrame(counts, columns=picks["Bracket"].values)
        df.insert(0, "Sim", np.arange(1, len(df) + 1))
        results[rnd] = df
        if total_counts is None:
            total_counts = counts.copy()
        else:
            total_counts += counts
    total_df = pd.DataFrame(total_counts, columns=picks["Bracket"].values)
    total_df.insert(0, "Sim", np.arange(1, len(total_df) + 1))
    results["Total"] = total_df
    return (
        results["R64"],
        results["R32"],
        results["S16"],
        results["E8"],
        results["F4"],
        results["Champ"],
        results["Total"])

@st.cache_data
def calculate_sim_ranks(scores_total):
    ranks_df = (
        scores_total.drop(columns="Sim")
        .rank(axis=1, ascending=False, method="min")
        .astype(int))
    ranks_df.insert(0, "Sim", np.arange(1, len(ranks_df) + 1))
    return ranks_df

def plot_correct_picks(counts_df, selected_bracket):
    counts = counts_df[selected_bracket]
    mean_val = counts.mean()
    min_val = counts.min()
    max_val = counts.max()
    bins = np.arange(min_val, max_val + 2)
    values, bins = np.histogram(counts, bins=bins)
    pct = values / values.sum() * 100
    x = bins[:-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=pct,
        marker_color='#009CDE',
        marker_line_width=0))
    fig.add_vline(
        x=mean_val,
        line_dash='dash',
        line_color='red',
        line_width=1.5)
    fig.update_layout(
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font_color='white',
        xaxis=dict(
            title='Number of Correct Picks',
            tickfont=dict(color='white'),
            gridcolor='#444444'),
        yaxis=dict(
            title='Probability (%)',
            ticksuffix='%',
            tickfont=dict(color='white'),
            gridcolor='#444444'),
        bargap=0,
        showlegend=False,
        margin=dict(l=50, r=20, t=20, b=50))
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def score_opening_rounds(picks, simulations, projections, day="Thu"):
    round_points = 1
    r64_cols = [f'R64_{i}' for i in range(1, 33)]
    seed_map = projections.set_index("Team")["Seed"]
    day_map = projections.set_index("Team")["R64Day"]
    sim_arr = simulations[r64_cols].values
    picks_arr = picks[r64_cols].values
    seed_values = np.vectorize(lambda x: seed_map.get(x, 0))(picks_arr)
    pick_points = seed_values + round_points
    match = sim_arr[:, None, :] == picks_arr[None, :, :]
    scores = (match * pick_points[None, :, :])
    day_values = np.vectorize(lambda x: day_map.get(x, None))(picks_arr)
    day_mask = (day_values == day)
    scores = (scores * day_mask[None, :, :]).sum(axis=2)
    df = pd.DataFrame(scores, columns=picks["Bracket"].values)
    df.insert(0, "Sim", np.arange(1, len(df) + 1))
    return df

@st.cache_data
def count_opening_round_simulations(picks, simulations, projections, day="Thu"):
    r64_cols = [f'R64_{i}' for i in range(1, 33)]
    day_map = projections.set_index("Team")["R64Day"]
    picks_arr = picks[r64_cols].values
    sim_arr = simulations[r64_cols].values
    day_values = np.vectorize(lambda x: day_map.get(x, None))(picks_arr)
    day_mask = (day_values == day)
    match = sim_arr[:, None, :] == picks_arr[None, :, :]
    counts = (match * day_mask[None, :, :]).sum(axis=2)
    df = pd.DataFrame(counts, columns=picks["Bracket"].values)
    df.insert(0, "Sim", np.arange(1, len(df) + 1))
    return df

@st.cache_data
def score_simulations_by_region(picks, simulations, projections, region):
    round_points = {'R64': 1, 'R32': 3, 'S16': 6, 'E8': 12}
    round_cols = {
        'R64': [f'R64_{i}' for i in range(1, 33)],
        'R32': [f'R32_{i}' for i in range(1, 17)],
        'S16': [f'S16_{i}' for i in range(1, 9)],
        'E8':  [f'E8_{i}' for i in range(1, 5)]}
    seed_map = projections.set_index("Team")["Seed"]
    region_map = projections.set_index("Team")["Region"]
    total_scores = None
    for rnd, cols in round_cols.items():
        sim_arr = simulations[cols].values
        picks_arr = picks[cols].values
        seed_values = np.vectorize(lambda x: seed_map.get(x, 0))(picks_arr)
        region_values = np.vectorize(lambda x: region_map.get(x, None))(picks_arr)
        pick_points = seed_values + round_points[rnd]
        match = sim_arr[:, None, :] == picks_arr[None, :, :]
        region_mask = (region_values == region)
        scores = (match * pick_points[None, :, :] * region_mask[None, :, :]).sum(axis=2)
        if total_scores is None:
            total_scores = scores.copy()
        else:
            total_scores += scores
    df = pd.DataFrame(total_scores, columns=picks["Bracket"].values)
    df.insert(0, "Sim", np.arange(1, len(df) + 1))
    return df

@st.cache_data
def count_simulations_by_region(picks, simulations, projections, region):
    round_cols = {
        'R64': [f'R64_{i}' for i in range(1, 33)],
        'R32': [f'R32_{i}' for i in range(1, 17)],
        'S16': [f'S16_{i}' for i in range(1, 9)],
        'E8':  [f'E8_{i}' for i in range(1, 5)]}
    region_map = projections.set_index("Team")["Region"]
    total_counts = None
    for rnd, cols in round_cols.items():
        sim_arr = simulations[cols].values
        picks_arr = picks[cols].values
        region_values = np.vectorize(lambda x: region_map.get(x, None))(picks_arr)
        match = sim_arr[:, None, :] == picks_arr[None, :, :]
        region_mask = (region_values == region)
        counts = (match * region_mask[None, :, :]).sum(axis=2)
        if total_counts is None:
            total_counts = counts.copy()
        else:
            total_counts += counts
    df = pd.DataFrame(total_counts, columns=picks["Bracket"].values)
    df.insert(0, "Sim", np.arange(1, len(df) + 1))
    return df

def calculate_expected_value(Scores, Counts, payout, Type):
    payout = np.array(payout)
    score_vals = Scores.iloc[:, 1:].values
    count_vals = Counts.iloc[:, 1:].values
    n_sims, n_brackets = score_vals.shape
    total_returns = np.zeros(n_brackets)
    for s in range(n_sims):
        order = np.argsort(-score_vals[s])
        sorted_counts = count_vals[s][order]
        tie_order = np.argsort(-sorted_counts, kind="stable")
        final_order = order[tie_order]
        ranked_payout = payout[:n_brackets]
        total_returns[final_order] += ranked_payout
    expected_values = total_returns / n_sims
    return pd.DataFrame({
        "Bracket": Scores.columns[1:],
        Type: expected_values
    })

def build_games_table(projections):
    games = []
    rounds = ["R64", "R32", "S16", "E8", "F4", "Champ"]
    for rnd in rounds:
        group_col = f"{rnd}Group"
        if rnd == "Champ":
            continue
        groups = projections[group_col].unique()
        for g in groups:
            teams = projections[projections[group_col] == g]

            if len(teams) == 2:
                games.append({
                    "GameID": f"{rnd}_{g}",
                    "Round": rnd,
                    "TeamA": teams.iloc[0]["Team"],
                    "TeamB": teams.iloc[1]["Team"]
                })
    return pd.DataFrame(games)

def build_payout_matrix(ScoresFinal, ScoresCounts, payout):
    payout = np.array(payout)
    scores = ScoresFinal.values
    counts = ScoresCounts.values
    order = np.argsort(-scores, axis=1)
    row_idx = np.arange(scores.shape[0])[:, None]
    tied_counts = counts[row_idx, order]
    count_order = np.argsort(-tied_counts, axis=1)
    final_order = order[row_idx, count_order]
    payout_matrix = payout[final_order]
    return payout_matrix

def build_ev_table(Projections2, ScoresTotal, CountsTotal, simulations, payout, Type):

    ScoresTotal = ScoresTotal.drop(columns=["Sim"], errors="ignore")
    CountsTotal = CountsTotal.drop(columns=["Sim"], errors="ignore")

    PayoutMatrix = build_payout_matrix(ScoresTotal, CountsTotal, payout)
    results = []
    brackets = range(PayoutMatrix.shape[1])
    for _, game in Projections2.iterrows():
        game_id = game["GameID"]
        team_a = game["TeamA"]
        team_b = game["TeamB"]
        sim_col = simulations[game_id].values
        mask_a = sim_col == team_a
        mask_b = sim_col == team_b
        if mask_a.sum() == 0 or mask_b.sum() == 0:
            continue
        ev_a = PayoutMatrix[mask_a].mean(axis=0)
        ev_b = PayoutMatrix[mask_b].mean(axis=0)
        ev_diff = ev_a - ev_b
        for j in brackets:
            results.append([
                game_id,
                PayoutMatrix.shape[1] and j,
                ev_a[j],
                ev_b[j],
                ev_diff[j],
                Type])
    return pd.DataFrame(
        results,
        columns=["GameID", "Bracket", "EV_A", "EV_B", "EV_Diff", "Type"])

def get_total_payout(ScoresTotal, CountsTotal, Projections2, ScoresThurs, CountsThurs, Sims, ScoresFri, CountsFri, ScoresWest, CountsWest, ScoresEast, CountsEast, ScoresSouth, CountsSouth, ScoresMidwest, CountsMidwest, Scores32, Counts32, Picks, Projections):
    payout = [2000/34] * 33 + [10000] * 1 + [0] * 103
    ExpTotal = calculate_expected_value(ScoresTotal, CountsTotal, payout, "Total")
    TotalPayoutOutput = build_ev_table(Projections2, ScoresTotal, CountsTotal, Sims, payout, "Total")
    payout = [10] * 1 + [0] * 136
    ExpThurs = calculate_expected_value(ScoresThurs, CountsThurs, payout, "Thurs")
    ThursPayoutOutput = build_ev_table(Projections2, ScoresThurs, CountsThurs, Sims, payout, "Thurs")
    payout = [10] * 1 + [0] * 136
    ExpFri = calculate_expected_value(ScoresFri, CountsFri, payout, "Fri")
    FriPayoutOutput = build_ev_table(Projections2, ScoresFri, CountsFri, Sims, payout, "Fri")
    payout = [10] * 1 + [0] * 136
    ExpWest = calculate_expected_value(ScoresWest, CountsWest, payout, "West")
    WestPayoutOutput = build_ev_table(Projections2, ScoresWest, CountsWest, Sims, payout, "West")
    payout = [10] * 1 + [0] * 136
    ExpEast = calculate_expected_value(ScoresEast, CountsEast, payout, "East")
    EastPayoutOutput = build_ev_table(Projections2, ScoresEast, CountsEast, Sims, payout, "East")
    payout = [10] * 1 + [0] * 136
    ExpSouth = calculate_expected_value(ScoresSouth, CountsSouth, payout, "South")
    SouthPayoutOutput = build_ev_table(Projections2, ScoresSouth, CountsSouth, Sims, payout, "South")
    payout = [10] * 1 + [0] * 136
    ExpMidwest = calculate_expected_value(ScoresMidwest, CountsMidwest, payout, "Midwest")
    MidwestPayoutOutput = build_ev_table(Projections2, ScoresMidwest, CountsMidwest, Sims, payout, "Midwest")
    payout = [10] * 1 + [0] * 136
    ExpS16 = calculate_expected_value(Scores32, Counts32, payout, "S16")
    S16PayoutOutput = build_ev_table(Projections2, Scores32, Counts32, Sims, payout, "S16")
    exp_tables = [
        ExpTotal, ExpThurs, ExpFri,
        ExpWest, ExpEast, ExpSouth,
        ExpMidwest, ExpS16]
    ExpCombined = reduce(
        lambda left, right: pd.merge(left, right, on="Bracket", how="left"),
        exp_tables)
    payout_tables = [
        TotalPayoutOutput, ThursPayoutOutput, FriPayoutOutput,
        WestPayoutOutput, EastPayoutOutput, SouthPayoutOutput,
        MidwestPayoutOutput, S16PayoutOutput]
    PayoutCombined = pd.concat(payout_tables, axis=0, ignore_index=True)
    PayoutCombined = (
    PayoutCombined
    .groupby(["GameID", "Bracket"], as_index=False)
    .agg({
        "EV_A": "sum",
        "EV_B": "sum"}))
    PayoutCombined["EV_Diff"] = PayoutCombined["EV_B"] - PayoutCombined["EV_A"]
    PayoutCombined["Bracket"] = np.tile(Picks["Bracket"].values, len(PayoutCombined) // len(Picks))
    PayoutCombined = PayoutCombined.merge(Projections2[["GameID", "TeamA", "TeamB"]], on="GameID", how="left")
    PayoutCombined = PayoutCombined.merge(Projections[["Team", "Seed", "ActualName", "Logo", "Record", "Color"]], left_on="TeamA", right_on="Team", how="left", suffixes=("", "_a")).drop(columns="Team")
    PayoutCombined = PayoutCombined.merge(Projections[["Team", "Seed", "ActualName", "Logo", "Record", "Color"]], left_on="TeamB", right_on="Team", how="left", suffixes=("", "_b")).drop(columns="Team")
    PayoutCombined["Record"] = ("No. " + PayoutCombined["Seed"].astype(str) + " " + PayoutCombined["Record"])
    PayoutCombined["Record_b"] = ("No. " + PayoutCombined["Seed_b"].astype(str) + " " + PayoutCombined["Record_b"])
    PayoutCombined = PayoutCombined[["Bracket",  "ActualName", "ActualName_b", "Logo", "Logo_b", "Record", "Record_b", "Color", "Color_b", "EV_A", "EV_B", "EV_Diff"]]
    return ExpCombined, PayoutCombined


def render_ev_matchup(df, RowNumber):

    row = df.iloc[RowNumber]

    team_a   = row["ActualName"]
    team_b   = row["ActualName_b"]
    logo_a   = row["Logo"]
    logo_b   = row["Logo_b"]
    record_a = row["Record"]
    record_b = row["Record_b"]
    color_a  = row["Color"]
    color_b  = row["Color_b"]
    ev_a     = row["EV_A"]
    ev_b     = row["EV_B"]
    ev_diff  = row["EV_Diff"]

    # ── normalize indicator position ─────────────────────────────────────────
    # Map ev_diff onto [-1, 1] using the sum of absolute EVs as scale.
    # Clamp to avoid extreme edge cases.
    scale = abs(ev_a) + abs(ev_b)
    if scale == 0:
        norm = 0.0
    else:
        norm = max(-1.0, min(1.0, ev_diff / scale))

    # Convert norm [-1,1] → bar percentage [0,100], center = 50
    indicator_pct = 50 + norm * 45  # max 5% padding from edges

    # ── logo src helper ───────────────────────────────────────────────────────
    def logo_src(path):
        if path.startswith("http"):
            return path
        import base64 
        import pathlib
        data = pathlib.Path(path).read_bytes()
        ext = pathlib.Path(path).suffix.lstrip(".")
        mime = "png" if ext == "png" else "jpeg" if ext in ("jpg", "jpeg") else "png"
        return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

    src_a = logo_src(logo_a)
    src_b = logo_src(logo_b) ##A

    # ── dollar formatting ─────────────────────────────────────────────────────
    def fmt(v):
        return f"${abs(v):.2f}"

    label_a = fmt(ev_a)
    label_b = fmt(ev_b)

    # Which side has the edge?
    edge_side = "A" if ev_diff > 0 else "B" if ev_diff < 0 else None
    edge_color = color_a if edge_side == "A" else color_b if edge_side == "B" else "#ffffff"

    html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
      .ev-root {{
        font-family: 'Barlow', sans-serif;
        background: #0a0a0f;
        border-radius: 16px;
        overflow: visible;
        position: relative;
        box-shadow:
          0 0 0 1px rgba(255,255,255,0.06),
          0 32px 80px rgba(0,0,0,0.7),
          0 8px 24px rgba(0,0,0,0.5);
        margin-bottom: 8px;
        padding: 20px 24px 28px;
      }}

      /* grain overlay */
      .ev-root::before {{
        content: '';
        position: absolute;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
        opacity: 0.35;
        pointer-events: none;
        z-index: 0;
        border-radius: 16px;
      }}

      /* split background glow */
      .ev-glow-left {{
        position: absolute; left: -5%; top: -20%;
        width: 50%; height: 140%;
        background: radial-gradient(ellipse at 20% 50%, {color_a}55 0%, transparent 60%);
        pointer-events: none; z-index: 0; filter: blur(4px);
      }}
      .ev-glow-right {{
        position: absolute; right: -5%; top: -20%;
        width: 50%; height: 140%;
        background: radial-gradient(ellipse at 80% 50%, {color_b}55 0%, transparent 60%);
        pointer-events: none; z-index: 0; filter: blur(4px);
      }}

      /* teams row */
      .ev-teams {{
        position: relative; z-index: 5;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 22px;
      }}

      .ev-team {{
        display: flex;
        align-items: center;
        gap: 14px;
        flex: 1;
      }}
      .ev-team.right {{
        flex-direction: row-reverse;
        text-align: right;
      }}

      .ev-logo {{
        width: 72px; height: 72px;
        object-fit: contain;
        flex-shrink: 0;
        filter: drop-shadow(0 4px 16px rgba(0,0,0,0.6));
      }}

      .ev-team-info {{ line-height: 1.2; }}

      .ev-team-name {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 26px; font-weight: 900;
        text-transform: uppercase;
        color: #ffffff;
        letter-spacing: 0.5px;
        display: block; line-height: 1;
      }}
      .ev-team-record {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px; font-weight: 600;
        letter-spacing: 2px;
        color: rgba(255,255,255,0.35);
        display: block; margin-top: 4px;
        text-transform: uppercase;
      }}

      /* VS badge */
      .ev-vs {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 13px; font-weight: 700;
        letter-spacing: 3px;
        color: rgba(255,255,255,0.2);
        padding: 0 20px;
        flex-shrink: 0;
      }}

      /* ── mobile: stack teams vertically ── */
      @media (max-width: 520px) {{
        .ev-teams {{
          flex-direction: column;
          gap: 0;
          margin-bottom: 16px;
        }}
        .ev-team {{
          flex-direction: row !important;
          text-align: left !important;
          width: 100%;
          padding: 10px 0;
        }}
        .ev-team.right {{
          flex-direction: row-reverse !important;
          text-align: right !important;
          border-top: 1px solid rgba(255,255,255,0.07);
        }}
        .ev-logo {{
          width: 52px; height: 52px;
        }}
        .ev-team-name {{
          font-size: 20px;
        }}
        .ev-vs {{
          display: none;
        }}
      }}

      /* ── EV bar section ── */
      .ev-bar-section {{
        position: relative; z-index: 5;
        margin-top: 8px;
      }}

      /* label row above bar */
      .ev-labels {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 10px;
      }}
      .ev-label {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px; font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.4);
      }}
      .ev-amount {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 22px; font-weight: 900;
        letter-spacing: -0.5px;
        display: block; line-height: 1;
      }}
      .ev-amount.a {{ color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.2); }}
      .ev-amount.b {{ color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.2); }}

      .ev-label-block {{ display: flex; flex-direction: column; gap: 3px; }}
      .ev-label-block.right {{ text-align: right; }}

      /* the track */
      .ev-track {{
        position: relative;
        height: 8px;
        border-radius: 99px;
        background: rgba(255,255,255,0.08);
        overflow: visible;
      }}

      /* left fill (Team A color) */
      .ev-fill-a {{
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: {indicator_pct}%;
        border-radius: 99px 0 0 99px;
        background: linear-gradient(90deg, {color_a}99, {color_a}dd);
        transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
      }}

      /* right fill (Team B color) */
      .ev-fill-b {{
        position: absolute;
        right: 0; top: 0; bottom: 0;
        width: {100 - indicator_pct}%;
        border-radius: 0 99px 99px 0;
        background: linear-gradient(270deg, {color_b}99, {color_b}dd);
        transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
      }}

      /* glowing indicator dot */
      .ev-indicator {{
        position: absolute;
        top: 50%;
        left: {indicator_pct}%;
        transform: translate(-50%, -50%);
        width: 20px; height: 20px;
        border-radius: 50%;
        background: {edge_color};
        box-shadow:
          0 0 0 3px rgba(10,10,15,0.9),
          0 0 0 5px {edge_color}66,
          0 0 20px 6px {edge_color}88,
          0 0 40px 12px {edge_color}44;
        z-index: 10;
        animation: indicatorPulse 2s ease-in-out infinite;
      }}

      @keyframes indicatorPulse {{
        0%, 100% {{ box-shadow:
          0 0 0 3px rgba(10,10,15,0.9),
          0 0 0 5px {edge_color}66,
          0 0 20px 6px {edge_color}88,
          0 0 40px 12px {edge_color}44; }}
        50% {{ box-shadow:
          0 0 0 3px rgba(10,10,15,0.9),
          0 0 0 6px {edge_color}99,
          0 0 30px 10px {edge_color}aa,
          0 0 60px 20px {edge_color}55; }}
      }}

      .ev-callout {{
        position: absolute;
        left: {indicator_pct}%;
        bottom: 100%;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 6px;
        pointer-events: none;
      }}
      .ev-callout-bubble {{
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        color: #ffffff;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 13px; font-weight: 700;
        letter-spacing: 0.5px;
        padding: 4px 12px;
        border-radius: 6px;
        white-space: nowrap;
        margin-bottom: 4px;
      }}
      .ev-callout-line {{
        width: 2px;
        height: 10px;
        background: linear-gradient(rgba(255,255,255,0.4), transparent);
        border-radius: 1px;
      }}

      /* bottom team name labels under bar */
      .ev-bar-labels {{
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
      }}
      .ev-bar-team-label {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 10px; font-weight: 700;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.25);
      }}

      /* color accent stripes on the card edges */
      .ev-stripe-a {{
        position: absolute; left: 0; top: 0; bottom: 0;
        width: 4px; border-radius: 16px 0 0 16px;
        background: {color_a};
        box-shadow: 2px 0 16px {color_a}88;
      }}
      .ev-stripe-b {{
        position: absolute; right: 0; top: 0; bottom: 0;
        width: 4px; border-radius: 0 16px 16px 0;
        background: {color_b};
        box-shadow: -2px 0 16px {color_b}88;
      }}
    </style>

    <div class="ev-root">
      <div class="ev-stripe-a"></div>
      <div class="ev-stripe-b"></div>
      <div class="ev-glow-left"></div>
      <div class="ev-glow-right"></div>

      <!-- Teams -->
      <div class="ev-teams">
        <div class="ev-team left">
          <img class="ev-logo" src="{src_a}" alt="{team_a}" onerror="this.style.opacity='0.3'" />
          <div class="ev-team-info">
            <span class="ev-team-name">{team_a}</span>
            <span class="ev-team-record">{record_a}</span>
          </div>
        </div>

        <div class="ev-vs">VS</div>

        <div class="ev-team right">
          <img class="ev-logo" src="{src_b}" alt="{team_b}" onerror="this.style.opacity='0.3'" />
          <div class="ev-team-info">
            <span class="ev-team-name">{team_b}</span>
            <span class="ev-team-record">{record_b}</span>
          </div>
        </div>
      </div>

      <!-- EV Bar -->
      <div class="ev-bar-section">
        <!-- Dollar labels above bar -->
        <div class="ev-labels">
          <div class="ev-label-block">
            <span class="ev-label">If {team_a} wins</span>
            <span class="ev-amount a">{label_a}</span>
          </div>
          <div class="ev-label-block right">
            <span class="ev-label">If {team_b} wins</span>
            <span class="ev-amount b">{label_b}</span>
          </div>
        </div>

        <!-- Track with fills and indicator -->
        <div style="position:relative; padding-top: 40px;">
          <!-- Callout above indicator -->
          <div class="ev-callout">
            <div class="ev-callout-bubble">
                ${abs(ev_diff):.2f}
            </div>
            <div class="ev-callout-line"></div>
          </div>

          <div class="ev-track">
            <div class="ev-fill-a"></div>
            <div class="ev-fill-b"></div>
            <div class="ev-indicator"></div>
          </div>
        </div>

        <!-- Team name labels under bar -->
        <div class="ev-bar-labels">
          <span class="ev-bar-team-label">◀ {team_a}</span>
          <span class="ev-bar-team-label">{team_b} ▶</span>
        </div>
      </div>
    </div>
    """

    components.html(html, height=380, scrolling=False)