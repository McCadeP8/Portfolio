#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_expected_points, calculate_risk_score, run_simulations, calculate_finish_chances, score_simulations, plot_correct_picks

projections = get_projections()
picks = get_picks()
expected_points = calculate_expected_points(projections, picks)
RiskScore = calculate_risk_score(projections, picks)
sims   = run_simulations(projections, n_simulations=10000)
scores = score_simulations(picks, sims, projections)
finish = calculate_finish_chances(scores)

st.title("Kirk's March Madness Bracket Analysis")

selected_bracket = st.selectbox('Select Bracket', picks['Bracket'].unique())
round_name = st.selectbox('Select Round', ['All', 'R64', 'R32', 'S16', 'E8', 'F4', 'Champ'])
plot_correct_picks(picks, sims, selected_bracket, round_name)