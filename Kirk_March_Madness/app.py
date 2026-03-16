#import os
#os.chdir("Kirk_March_Madness")

import streamlit as st
from data import get_projections, get_picks, calculate_risk_score, run_simulations, plot_correct_picks, get_projections2, render_ev_matchup, get_risk_value, update_total_expected, render_bracket, run_analysis, get_sims_pre, actual_results, get_scores_dataframe


st.set_page_config(
    page_title = "Kirk's March Madness Bracket Analysis",
    page_icon = ":basketball:",
    layout = "wide")

st.title(":basketball::trophy: Kirk's March Madness Pool:trophy::basketball:")

with st.spinner("In Progress"):
    Projections = get_projections()
    Picks = get_picks(Projections)
    Projections["Team"] = Projections["ActualName"]
    Projections2 = get_projections2()
    RiskScore = calculate_risk_score(Projections, Picks)
    Sims = run_simulations(Projections, n_simulations=20000)
    ActualResults = actual_results(Sims)
#   Sims.to_parquet("SimsPre.parquet", index=False)
    SimsPre = get_sims_pre()
    (Scores64, Scores32, Scores16, Scores8, Scores4, Scores2, ScoresTotal,
    Counts64, Counts32, Counts16, Counts8, Counts4, Counts2, CountsTotal,
    Finish,
    ScoresThurs, ScoresFri, CountsThurs, CountsFri,
    ScoresWest, ScoresEast, ScoresSouth, ScoresMidwest,
    CountsWest, CountsEast, CountsSouth, CountsMidwest,
    TotalExpected, TotalPayout,
    ExpectedDF) = run_analysis(Sims, Projections, Projections2, Picks)

    (Scores64Pre, Scores32Pre, Scores16Pre, Scores8Pre, Scores4Pre, Scores2Pre, ScoresTotalPre,
    Counts64Pre, Counts32Pre, Counts16Pre, Counts8Pre, Counts4Pre, Counts2Pre, CountsTotalPre,
    FinishPre,
    ScoresThursPre, ScoresFriPre, CountsThursPre, CountsFriPre,
    ScoresWestPre, ScoresEastPre, ScoresSouthPre, ScoresMidwestPre,
    CountsWestPre, CountsEastPre, CountsSouthPre, CountsMidwestPre,
    TotalExpectedPre, TotalPayoutPre,
    ExpectedDFPre) = run_analysis(SimsPre, Projections, Projections2, Picks)

    ActualResultsExp = get_scores_dataframe(ActualResults, Projections, Projections2, Picks)

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

    with tab4:
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

        sections = [
        ("Total", "Total_Score", "Total_Count", ScoresTotalPre, CountsTotalPre),
        ("Thursday", "Thurs_Score", "Thurs_Count", ScoresThursPre, CountsThursPre),
        ("Friday", "Fri_Score", "Fri_Count", ScoresFriPre, CountsFriPre),
        ("East Region", "East_Score", "East_Count", ScoresEastPre, CountsEastPre),
        ("West Region", "West_Score", "West_Count", ScoresWestPre, CountsWestPre),
        ("South Region", "South_Score", "South_Count", ScoresSouthPre, CountsSouthPre),
        ("Midwest Region", "Midwest_Score", "Midwest_Count", ScoresMidwestPre, CountsMidwestPre),
        ("Round of 64", "Round of 64_Score", "Round of 64_Count", Scores64Pre, Counts64Pre),
        ("Round of 32", "Round of 32_Score", "Round of 32_Count", Scores32Pre, Counts32Pre),
        ("Sweet Sixteen", "Sweet 16_Score", "Sweet 16_Count", Scores16Pre, Counts16Pre),
        ("Elite Eight", "Elite 8_Score", "Elite 8_Count", Scores8Pre, Counts8Pre),
        ("Final Four", "Final Four_Score", "Final Four_Count", Scores4Pre, Counts4Pre),
        ("Champion", "Championship_Score", "Championship_Count", Scores2Pre, Counts2Pre)]


        for title, score_col, count_col, score_df, count_df in sections:

            st.subheader(title)
            col10, col11, col12 = st.columns([1,2,2])
            actualS = get_risk_value(ActualResultsExp, selected_bracket, score_col)
            expectedS = get_risk_value(ExpectedDFPre, selected_bracket, score_col)
            actualC = get_risk_value(ActualResultsExp, selected_bracket, count_col)
            expectedC = get_risk_value(ExpectedDFPre, selected_bracket, count_col)

            with col10:
                st.metric(label="Points", value=actualS, delta=round(actualS - expectedS, 2), border=True)
                st.metric(label="Correct", value=actualC, delta=round(actualC - expectedC, 2), border=True)
            with col11:
                plot_correct_picks(score_df, selected_bracket, f"Distribution of {title} Points", actualS)
            with col12:
                plot_correct_picks(count_df, selected_bracket, f"Distribution of {title} Correct Picks", actualC)
        
    with tab5:
        render_bracket(Projections, Picks, selected_bracket)

with tab2:
    OverallData = update_total_expected(TotalExpected, ScoresTotal, CountsTotal, RiskScore, Picks, Finish, ActualResultsExp)
    st.dataframe(
        OverallData,
        use_container_width=True, height="content", hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn(format="%.0f"),
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