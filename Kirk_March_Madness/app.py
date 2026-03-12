#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
import numpy as np
from data import get_projections, get_picks, calculate_expected_points, calculate_risk_score, run_simulations, calculate_finish_chances, score_simulations, plot_correct_picks, compute_all_results, compute_all_results_p, plot_correct_picks_p

st.set_page_config(
    page_title = "Kir's March Madness Bracket Analysis",
    page_icon = ":basketball:",
    layout = "wide")

projections = get_projections()
picks = get_picks()
expected_points = calculate_expected_points(projections, picks)
RiskScore = calculate_risk_score(projections, picks)
sims   = run_simulations(projections, n_simulations=10000)
scores = score_simulations(picks, sims, projections)
finish = calculate_finish_chances(scores)
AllResults = compute_all_results(picks, sims)
AllPoints = compute_all_results_p(picks, sims)

        
selected_bracket = st.selectbox('Select Bracket', picks['Bracket'].unique())
for round_name in ['R64', 'R32', 'S16', 'E8', 'F4', 'Champ']:
    col1, col2 = st.columns(2)
    with col1:
        plot_correct_picks(AllResults, selected_bracket, round_name)
    with col2:
        plot_correct_picks_p(AllPoints, selected_bracket, round_name)