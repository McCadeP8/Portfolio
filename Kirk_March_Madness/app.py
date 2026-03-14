#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, plot_correct_picks, build_games_table, render_ev_matchup, get_risk_value, update_total_expected, render_bracket, run_analysis, get_sims_pre

st.set_page_config(
    page_title = "Kirk's March Madness Bracket Analysis",
    page_icon = ":basketball:",
    layout = "wide")

st.title(":basketball::trophy: Kirk's March Madness Pool:trophy::basketball:")

with st.spinner("In Progress"):
    Projections = get_projections()
    Projections2 = build_games_table(Projections)
    Picks = get_picks(Projections)
    Projections["Team"] = Projections["ActualName"]
    RiskScore = calculate_risk_score(Projections, Picks)
    Sims = run_simulations(Projections, n_simulations=10000)
#   Sims.to_parquet("SimsPre.parquet", index=False)
    SimsPre = get_sims_pre()
    (Scores64, Scores32, Scores16, Scores8, Scores4, Scores2, ScoresTotal,
    Counts64, Counts32, Counts16, Counts8, Counts4, Counts2, CountsTotal,
    Finish,
    ScoresThurs, ScoresFri, CountsThurs, CountsFri,
    ScoresWest, ScoresEast, ScoresSouth, ScoresMidwest,
    CountsWest, CountsEast, CountsSouth, CountsMidwest,
    TotalExpected, TotalPayout) = run_analysis(Sims, Projections, Projections2, Picks)

    (Scores64Pre, Scores32Pre, Scores16Pre, Scores8Pre, Scores4Pre, Scores2Pre, ScoresTotalPre,
    Counts64Pre, Counts32Pre, Counts16Pre, Counts8Pre, Counts4Pre, Counts2Pre, CountsTotalPre,
    FinishPre,
    ScoresThursPre, ScoresFriPre, CountsThursPre, CountsFriPre,
    ScoresWestPre, ScoresEastPre, ScoresSouthPre, ScoresMidwestPre,
    CountsWestPre, CountsEastPre, CountsSouthPre, CountsMidwestPre,
    TotalExpectedPre, TotalPayoutPre) = run_analysis(SimsPre, Projections, Projections2, Picks)

tab1, tab2 = st.tabs(["Bracket Outlook", "Overall Standings"])

with tab1:
    selected_bracket = st.selectbox('Select Bracket', Picks['Bracket'].unique())
    tab3, tab4, tab5 = st.tabs(["Cheering Guide", "Bracket Performance", f"{selected_bracket}'s Bracket"])
    with tab3:
        col1, col2 = st.columns(2)
        render_df = (
        TotalPayout[TotalPayout["Bracket"] == selected_bracket]
        .assign(AbsEV=lambda x: x["EV_Diff"].abs())
        .sort_values("AbsEV", ascending=False)
        .reset_index(drop=True))

    with col1:
        for i in range(0, len(render_df), 2):
            render_ev_matchup(render_df, i)

    with col2:
        for i in range(1, len(render_df), 2):
            render_ev_matchup(render_df, i)

    with tab4: #A
        st.subheader("Overall Outlook")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            risk_value = round(float(get_risk_value(RiskScore, selected_bracket, "risk_score")), 1)
            risk_rank  = f"#{int(get_risk_value(RiskScore, selected_bracket, 'risk_rank'))} Overall"
            st.metric(label="Overall Risk Score", value=risk_value, delta=risk_rank,
                    help="Composite score blending downside, concentration, and upset risk. Higher = more aggressive bracket.",
                    border=True)

        with col2:
            downside_value = round(float(get_risk_value(RiskScore, selected_bracket, "downside")), 1)
            downside_rank  = f"#{int(get_risk_value(RiskScore, selected_bracket, 'downside_rank'))} Overall"
            st.metric(label="Downside Risk", value=downside_value, delta=downside_rank,
                    help="Total points at risk across all picks, weighted by loss probability. Higher = more points riding on unlikely outcomes.",
                    border=True)

        with col3:
            concentration_value = round(float(get_risk_value(RiskScore, selected_bracket, "champ_concentration")), 1)
            concentration_rank  = f"#{int(get_risk_value(RiskScore, selected_bracket, 'concentration_rank'))} Overall"
            st.metric(label="Champion Risk", value=concentration_value, delta=concentration_rank,
                    help="Percentage of expected points coming from your champion pick. Higher = bracket lives and dies with one team.",
                    border=True)

        with col4:
            upset_value = round(float(get_risk_value(RiskScore, selected_bracket, "avg_upset_seed")), 2)
            upset_rank  = f"#{int(get_risk_value(RiskScore, selected_bracket, 'upset_score_rank'))} Overall"
            st.metric(label="Upset Risk", value=upset_value, delta=upset_rank,
                    help="Weighted average seed of teams picked to win each round. Higher = more Cinderella picks.",
                    border=True)

        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresTotalPre, selected_bracket, "Distribution of Points")

        with col3:
            plot_correct_picks(CountsTotalPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Round of 64")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores64Pre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts64Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Round of 32")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores32Pre, selected_bracket, "Distribution of Points", 29)
        with col3:
            plot_correct_picks(Counts32Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Sweet Sixteen")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores16Pre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts16Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Elite Eight")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores8Pre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts8Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Final Four")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores4Pre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts4Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Championship")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(Scores2Pre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(Counts2Pre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Thursday")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresThursPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsThursPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Friday")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresFriPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsFriPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("West")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresWestPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsWestPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("East")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresEastPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsEastPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("South")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresSouthPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsSouthPre, selected_bracket, "Distribution of Correct Picks")

        st.subheader("Midwest")
        col1, col2, col3 = st.columns([1,2,2])
        with col1:
                st.metric(label="Points", value=29.4, delta=1.3, border=True)
                st.metric(label="Picks", value=4.8, delta=-0.5, border=True)
        with col2:
            plot_correct_picks(ScoresMidwestPre, selected_bracket, "Distribution of Points")
        with col3:
            plot_correct_picks(CountsMidwestPre, selected_bracket, "Distribution of Correct Picks")
    
    with tab5:
        render_bracket(Projections, Picks, selected_bracket)

with tab2:
    OverallData = update_total_expected(TotalExpected, ScoresTotal, CountsTotal, RiskScore, Picks, Finish)
    st.dataframe(
        OverallData,
        use_container_width=True, height="content", hide_index=True,
        column_config={
            "Pred. Pts": st.column_config.NumberColumn(format="%.2f"),
            "Pred. Games": st.column_config.NumberColumn(format="%.2f"),
            "Total EV": st.column_config.NumberColumn(format="$%.2f"),

            "Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "ITM%": st.column_config.NumberColumn(format="%.2f%%"),
            "Th Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "Fr Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "W Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "E Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "S Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "MW Win%": st.column_config.NumberColumn(format="%.2f%%"),
            "S16 Win%": st.column_config.NumberColumn(format="%.2f%%"),

            "Risk Score": st.column_config.NumberColumn(format="%.2f"),
            "Downside": st.column_config.NumberColumn(format="%.2f"),
            "Champ Risk": st.column_config.NumberColumn(format="%.2f"),
            "Avg. Upset": st.column_config.NumberColumn(format="%.2f")})