#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, calculate_sim_ranks, score_simulations_by_round, plot_correct_picks, count_simulations_by_round, score_opening_rounds, count_opening_round_simulations, score_simulations_by_region, count_simulations_by_region, build_games_table, render_ev_matchup, get_total_payout, get_risk_value

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



st.title(":basketball::trophy: Kirk's March Madness Pool:trophy::basketball:")

tab1, tab2 = st.tabs(["Bracket Outlook", "Overall Standings"])

with tab1:
    selected_bracket = st.selectbox('Select Bracket', Picks['Bracket'].unique())
    tab3, tab4 = st.tabs(["Cheering Guide", "Bracket Performance"])
    with tab3:
        col1, col2 = st.columns(2)
        render_df = (
        TotalPayout[TotalPayout["Bracket"] == selected_bracket]
        .assign(AbsEV=lambda x: x["EV_Diff"].abs())
        .sort_values("AbsEV", ascending=False)
        .reset_index(drop=True))

        with col1:
                render_ev_matchup(render_df, 0)
                render_ev_matchup(render_df, 2)
                render_ev_matchup(render_df, 4)
                render_ev_matchup(render_df, 6)
                render_ev_matchup(render_df, 8)
                render_ev_matchup(render_df, 10)
                render_ev_matchup(render_df, 12)
                render_ev_matchup(render_df, 14)
                render_ev_matchup(render_df, 16)
                render_ev_matchup(render_df, 18)
                render_ev_matchup(render_df, 20)
                render_ev_matchup(render_df, 22)
                render_ev_matchup(render_df, 24)
                render_ev_matchup(render_df, 26)
                render_ev_matchup(render_df, 28)
                render_ev_matchup(render_df, 30)#

        with col2:
                render_ev_matchup(render_df, 1)
                render_ev_matchup(render_df, 3)
                render_ev_matchup(render_df, 5)
                render_ev_matchup(render_df, 7)
                render_ev_matchup(render_df, 9)
                render_ev_matchup(render_df, 11)
                render_ev_matchup(render_df, 13)
                render_ev_matchup(render_df, 15)
                render_ev_matchup(render_df, 17)
                render_ev_matchup(render_df, 19)
                render_ev_matchup(render_df, 21)
                render_ev_matchup(render_df, 23)
                render_ev_matchup(render_df, 25)
                render_ev_matchup(render_df, 27)
                render_ev_matchup(render_df, 29)
                render_ev_matchup(render_df, 31)


    with tab4:
        st.subheader("Overall Outlook")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Overall Risk Score", value = get_risk_value(RiskScore, selected_bracket, "risk_score"), delta = get_risk_value(RiskScore, selected_bracket, "risk_rank"), help = "This score is calculated based on the probabilities of each pick being correct and the points awarded for each correct pick. A higher risk score indicates a more aggressive bracket with picks that are less likely to be correct but yield higher points.", border = True)
        with col2:
            plot_correct_picks(ScoresTotal, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsTotal, selected_bracket, "Distribution of Correct Picks")
        with col4:
            plot_correct_picks(CountsTotal, selected_bracket, "Distribution of Correct Picks")


        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresTotal, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsTotal, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Round of 64")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores64, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts64, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Round of 32")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores32, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts32, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Sweet Sixteen")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores16, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts16, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Elite Eight")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores8, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts8, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Final Four")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores4, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts4, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Championship")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(Scores2, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts2, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Thursday")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresThurs, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsThurs, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Friday")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresFri, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsFri, selected_bracket, "Distribution of Correct Picks")

        st.subheader("West")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresWest, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsWest, selected_bracket, "Distribution of Correct Picks")

        st.subheader("East")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresEast, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsEast, selected_bracket, "Distribution of Correct Picks")

        st.subheader("South")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresSouth, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsSouth, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Midwest")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Hello There")
        with col2:
            plot_correct_picks(ScoresMidwest, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsMidwest, selected_bracket, "Distribution of Correct Picks")


with tab2:
    st.write("Ehllo")