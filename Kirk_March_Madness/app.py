#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, calculate_sim_ranks, score_simulations_by_round, plot_correct_picks, count_simulations_by_round, score_opening_rounds, count_opening_round_simulations, score_simulations_by_region, count_simulations_by_region, calculate_expected_value, build_games_table, build_payout_matrix, build_ev_table, render_ev_matchup

st.set_page_config(
    page_title = "Kirk's March Madness Bracket Analysis",
    page_icon = ":basketball:",
    layout = "wide")

Projections = get_projections()
Projections2 = build_games_table(Projections)
Picks = get_picks()
RiskScore = calculate_risk_score(Projections, Picks)
Sims = run_simulations(Projections, n_simulations=10000)
Scores64, Scores32, Scores16, Scores8, Scores4, Scores2, ScoresTotal = score_simulations_by_round(Picks, Sims, Projections)
Counts64, Counts32, Counts16, Counts8, Counts4, Counts2, CountsTotal = count_simulations_by_round(Picks, Sims)
Finish = calculate_sim_ranks(ScoresTotal)
ScoresThurs = score_opening_rounds(Picks, Sims, Projections, "Thursday")
ScoresFri = score_opening_rounds(Picks, Sims, Projections, "Friday")
CountsThurs = count_opening_round_simulations(Picks, Sims, Projections, "Thursday")
CountsFri = count_opening_round_simulations(Picks, Sims, Projections, "Friday")
ScoresWest = score_simulations_by_region(Picks, Sims, Projections, "West")
ScoresEast = score_simulations_by_region(Picks, Sims, Projections, "East")
ScoresSouth = score_simulations_by_region(Picks, Sims, Projections, "South")
ScoresMidwest = score_simulations_by_region(Picks, Sims, Projections, "Midwest")
CountWest = count_simulations_by_region(Picks, Sims, Projections, "West")
CountEast = count_simulations_by_region(Picks, Sims, Projections, "East")
CountSouth = count_simulations_by_region(Picks, Sims, Projections, "South")
CountMidwest = count_simulations_by_region(Picks, Sims, Projections, "Midwest")
payout = [2000/34] * 33 + [10000] * 1 + [0] * 103
ExpTotal = calculate_expected_value(ScoresTotal, CountsTotal, payout)
TotalPayoutMatrix = build_payout_matrix(ScoresTotal, CountsTotal, payout)
TotalPayoutOutput = build_ev_table(Projections2, Sims, TotalPayoutMatrix)

selected_bracket = st.selectbox('Select Bracket', Picks['Bracket'].unique())
st.subheader("Overall Outlook")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(ScoresTotal, selected_bracket)
with col3:
    plot_correct_picks(CountsTotal, selected_bracket)

st.subheader("Round of 64")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket)
with col3:
    plot_correct_picks(Counts64, selected_bracket)

st.subheader("Round of 32")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores32, selected_bracket)
with col3:
    plot_correct_picks(Counts32, selected_bracket)

st.subheader("Sweet Sixteen")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores16, selected_bracket)
with col3:
    plot_correct_picks(Counts16, selected_bracket)

st.subheader("Elite Eight")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores8, selected_bracket)
with col3:
    plot_correct_picks(Counts8, selected_bracket)

st.subheader("Final Four")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores4, selected_bracket)
with col3:
    plot_correct_picks(Counts4, selected_bracket)

st.subheader("Championship")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores2, selected_bracket)
with col3:
    plot_correct_picks(Counts2, selected_bracket)

col1, col2 = st.columns(2)
with col1:
        render_ev_matchup(
        team_a="Duke",
        team_b="Kentucky",
        logo_a="https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2750.png&h=200&w=200",
        logo_b="https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2750.png&h=200&w=200",
        record_a="30-4",
        record_b="26-8",
        color_a="#003087",
        color_b="#0033A0",
        ev_a=2.45,
        ev_b=0.45,
        ev_diff=-1.85,
    )
with col2:
    render_ev_matchup(
        team_a="Duke Blue Devils",
        team_b="Kentucky Wildcats",
        logo_a="https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2750.png&h=200&w=200",
        logo_b="https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2750.png&h=200&w=200",
        record_a="No. 1 Sed (30-4)",
        record_b="No. 4 Seed (26-8)",
        color_a="#000000",
        color_b="#FF0000",
        ev_a=2.45,
        ev_b=0.45,
        ev_diff=1.80,
    )
