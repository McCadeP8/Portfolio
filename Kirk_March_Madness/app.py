#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, calculate_sim_ranks, score_simulations_by_round, plot_correct_picks, count_simulations_by_round

st.set_page_config(
    page_title = "Kirk's March Madness Bracket Analysis",
    page_icon = ":basketball:",
    layout = "wide")

Projections = get_projections()
Picks = get_picks()
RiskScore = calculate_risk_score(Projections, Picks)
Sims = run_simulations(Projections, n_simulations=10000)
Scores64, Scores32, Scores16, Scores8, Scores4, Scores2, ScoresTotal = score_simulations_by_round(Picks, Sims, Projections)
Counts64, Counts32, Counts16, Counts8, Counts4, Counts2, CountsTotal = count_simulations_by_round(Picks, Sims)
Finish = calculate_sim_ranks(ScoresTotal)

selected_bracket = st.selectbox('Select Bracket', Picks['Bracket'].unique())

col1, col2, col3 = st.columns(3)
st.subheader("Overall Outlook")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(ScoresTotal, selected_bracket, "Total")
with col3:
    plot_correct_picks(CountsTotal, selected_bracket, "Total")

col1, col2, col3 = st.columns(3)
st.subheader("Round of 64")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "R64")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "R64")

col1, col2, col3 = st.columns(3)
st.subheader("Round of 32")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "R32")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "R32")

col1, col2, col3 = st.columns(3)
st.subheader("Sweet Sixteen")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "S16")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "S16")

col1, col2, col3 = st.columns(3)
st.subheader("Elite Eight")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "E8")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "E8")

col1, col2, col3 = st.columns(3)
st.subheader("Final Four")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "F4")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "F4")

col1, col2, col3 = st.columns(3)
st.subheader("Championship")
with col1:
    st.write("Hello There")
with col2:
    plot_correct_picks(Scores64, selected_bracket, "Champ")
with col3:
    plot_correct_picks(Counts64, selected_bracket, "Champ")