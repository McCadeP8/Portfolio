#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, calculate_sim_ranks, score_simulations_by_round, plot_correct_picks, count_simulations_by_round, score_opening_rounds, count_opening_round_simulations, score_simulations_by_region, count_simulations_by_region, build_games_table, render_ev_matchup, get_total_payout

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
Scores2.insert(0, "Sim", range(1, len(Scores2) + 1))
Scores4.insert(0, "Sim", range(1, len(Scores2) + 1))
Scores8.insert(0, "Sim", range(1, len(Scores2) + 1))
Scores16.insert(0, "Sim", range(1, len(Scores2) + 1))
Scores32.insert(0, "Sim", range(1, len(Scores2) + 1))
Scores64.insert(0, "Sim", range(1, len(Scores2) + 1))
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
CountsWest = count_simulations_by_region(Picks, Sims, Projections, "West")
CountsEast = count_simulations_by_region(Picks, Sims, Projections, "East")
CountsSouth = count_simulations_by_region(Picks, Sims, Projections, "South")
CountsMidwest = count_simulations_by_region(Picks, Sims, Projections, "Midwest")
TotalExpected, TotalPayout = get_total_payout(ScoresTotal, CountsTotal, Projections2, ScoresThurs, CountsThurs, Sims, ScoresFri, CountsFri, ScoresWest, CountsWest, ScoresEast, CountsEast, ScoresSouth, CountsSouth, ScoresMidwest, CountsMidwest, Scores32, Counts32, Picks, Projections)



tab1, tab2 = st.tabs(["Bracket Outlook", "Overall Standings"])

with tab1:
    selected_bracket = st.selectbox('Select Bracket', Picks['Bracket'].unique())
    tab3, tab4 = st.tabs(["Cheering Guide", "Bracket Performance"])
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
                render_ev_matchup(selected_bracket, 1, TotalPayout)
        with col2:
                render_ev_matchup(selected_bracket, 2, TotalPayout)
    with tab4:
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


with tab2:
    st.write("Ehllo")


 