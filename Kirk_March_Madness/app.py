#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
import numpy as np
from data import get_projections, get_picks, calculate_expected_points, calculate_risk_score, run_simulations, calculate_finish_chances, score_simulations, plot_correct_picks, compute_all_results

projections = get_projections()
picks = get_picks()
expected_points = calculate_expected_points(projections, picks)
RiskScore = calculate_risk_score(projections, picks)
sims   = run_simulations(projections, n_simulations=10000)
scores = score_simulations(picks, sims, projections)
finish = calculate_finish_chances(scores)
AllResults = compute_all_results(picks, sims)
    
    

st.title("Kirk's March Madness Bracket Analysis")
selected_bracket = st.selectbox('Select Bracket', picks['Bracket'].unique())
round_name = st.selectbox('Select Round', ['R64', 'R32', 'S16', 'E8', 'F4', 'Champ'])
plot_correct_picks(AllResults, selected_bracket, round_name)