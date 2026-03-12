#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_expected_points, calculate_risk_score, run_simulations, calculate_finish_chances, score_simulations

projections = get_projections()
picks = get_picks()
expected_points = calculate_expected_points()
RiskScore = calculate_risk_score()
sims   = run_simulations(projections, n_simulations=10000)
scores = score_simulations(picks, sims, projections)
finish = calculate_finish_chances(scores, top_n=20)
