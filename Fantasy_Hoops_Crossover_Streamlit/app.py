import streamlit as st
import re as re
from data import get_weekly_scores, get_schedule, get_teams, get_logo, get_team_schedule, get_base_records, get_conf_records, get_RPI, get_team_stat, points_per_game, get_quad_record, get_weighted_ppg, best_wins, get_final_table

st.set_page_config(
    page_title = "Fantasy Hoops Crossover",
    page_icon = ":basketball:",
    layout = "wide")

st.title(":basketball::trophy: NCAA/NBA College Hoops Crosover:trophy::basketball:")

teams = get_teams()
schedule = get_schedule()
scores = get_weekly_scores()
base_records = get_base_records(schedule, scores)
conf_records = get_conf_records(schedule, scores, teams)
RPI = get_RPI(base_records, schedule)
PPG = points_per_game(scores)
Quad1 = get_quad_record(schedule, scores, RPI, "Quad 1")
Quad2 = get_quad_record(schedule, scores, RPI, "Quad 2")
Quad3 = get_quad_record(schedule, scores, RPI, "Quad 3")
Quad4 = get_quad_record(schedule, scores, RPI, "Quad 4")
WPPG = get_weighted_ppg(scores)
FinalTable = get_final_table(base_records, conf_records, PPG, Quad1, Quad2, Quad3, Quad4, RPI, teams, WPPG)

tab1, tab2 = st.tabs(["All Stats", "Resume Comparison"])

with tab1:
    SelectedTeamAll = st.multiselect("Select All Teams", options=teams["Team"].tolist())
    if SelectedTeamAll:
        FinalTable = FinalTable[FinalTable["Team"].isin(SelectedTeamAll)]
    st.dataframe(FinalTable, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("")})

with tab2:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        SelectedTeam1 = st.selectbox("Select Team 1", options=teams["Team"].tolist(), index=teams["Team"].tolist().index("Jacksonville"))
        st.image(get_logo(teams, SelectedTeam1))

        col5, col6 = st.columns([1,1])
        with col5:
            st.metric(label = "Total Record", value = get_team_stat(base_records, SelectedTeam1, "Record"), delta = get_team_stat(base_records, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 2 Record", value = get_team_stat(Quad2, SelectedTeam1, "Record"), delta = get_team_stat(Quad2, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 3 Record", value = get_team_stat(Quad3, SelectedTeam1, "Record"), delta = get_team_stat(Quad3, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Ratings Power Index", value = get_team_stat(RPI, SelectedTeam1, "RPI"), delta = get_team_stat(RPI, SelectedTeam1, "RPI_Rk"), delta_color = "off", border = True)
            st.metric(label = "Points Per Week", value = get_team_stat(PPG, SelectedTeam1, "Avg Score"), delta = get_team_stat(PPG, SelectedTeam1, "PPG_Rk"), delta_color = "off", border = True)
            st.subheader("Best Wins")
            BestWins1 = best_wins(schedule, scores, teams, RPI, SelectedTeam1, "Win")
            st.dataframe(BestWins1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})        

        with col6:
            st.metric(label = "Conference Record", value = get_team_stat(conf_records, SelectedTeam1, "Record"), delta = get_team_stat(conf_records, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 1 Record", value = get_team_stat(Quad1, SelectedTeam1, "Record"), delta = get_team_stat(Quad1, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 4 Record", value = get_team_stat(Quad4, SelectedTeam1, "Record"), delta = get_team_stat(Quad4, SelectedTeam1, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Strength of Schedule", value = get_team_stat(RPI, SelectedTeam1, "SOS"), delta = get_team_stat(RPI, SelectedTeam1, "SOS_Rk"), delta_color = "off", border = True)
            st.metric(label = "Weighted Recent", value = get_team_stat(WPPG, SelectedTeam1, "Weighted"), delta = get_team_stat(WPPG, SelectedTeam1, "Weight_Rk"), delta_color = "off", border = True)
            st.subheader("Worst Losses")
            BestLoss1 = best_wins(schedule, scores, teams, RPI, SelectedTeam1, "Loss")
            st.dataframe(BestLoss1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

        st.subheader("Conference Games")
        CG1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Conf")
        st.dataframe(CG1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("OOC Tournament")
        OOC1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "OOC_Tourney")
        st.dataframe(OOC1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Tip-Off Tournament")
        TOT1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Tip-Off_Tourney")
        st.dataframe(TOT1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Mascot Challenge")
        M1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Mascot")
        st.dataframe(M1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Luck of the Draw")
        LOTD1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Luck")
        st.dataframe(LOTD1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Cross-Conference Showdown")
        CC1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Cross_Conf")
        st.dataframe(CC1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Best of the Best")
        BOB1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Best_Of_Best")
        st.dataframe(BOB1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Rivalry Week")
        R1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Rivalry")
        st.dataframe(R1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Regional Rights")
        RR1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Regional")
        st.dataframe(RR1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Conference Tournament")
        CT1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Conf_Tourney")
        st.dataframe(CT1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

    with col2:
        SelectedTeam2 = st.selectbox("Select Team 2", options=teams["Team"].tolist(), index=teams["Team"].tolist().index("Georgia"))
        st.image(get_logo(teams, SelectedTeam2))

        col7, col8 = st.columns([1,1])
        with col7:
            st.metric(label = "Total Record", value = get_team_stat(base_records, SelectedTeam2, "Record"), delta = get_team_stat(base_records, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 2 Record", value = get_team_stat(Quad2, SelectedTeam2, "Record"), delta = get_team_stat(Quad2, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 3 Record", value = get_team_stat(Quad3, SelectedTeam2, "Record"), delta = get_team_stat(Quad3, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Ratings Power Index", value = get_team_stat(RPI, SelectedTeam2, "RPI"), delta = get_team_stat(RPI, SelectedTeam2, "RPI_Rk"), delta_color = "off", border = True)
            st.metric(label = "Points Per Week", value = get_team_stat(PPG, SelectedTeam2, "Avg Score"), delta = get_team_stat(PPG, SelectedTeam2, "PPG_Rk"), delta_color = "off", border = True)
            st.subheader("Best Wins")
            BestWins2 = best_wins(schedule, scores, teams, RPI, SelectedTeam2, "Win")
            st.dataframe(BestWins2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})        

        with col8:
            st.metric(label = "Conference Record", value = get_team_stat(conf_records, SelectedTeam2, "Record"), delta = get_team_stat(conf_records, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 1 Record", value = get_team_stat(Quad1, SelectedTeam2, "Record"), delta = get_team_stat(Quad1, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 4 Record", value = get_team_stat(Quad4, SelectedTeam2, "Record"), delta = get_team_stat(Quad4, SelectedTeam2, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Strength of Schedule", value = get_team_stat(RPI, SelectedTeam2, "SOS"), delta = get_team_stat(RPI, SelectedTeam2, "SOS_Rk"), delta_color = "off", border = True)
            st.metric(label = "Weighted Recent", value = get_team_stat(WPPG, SelectedTeam2, "Weighted"), delta = get_team_stat(WPPG, SelectedTeam2, "Weight_Rk"), delta_color = "off", border = True)
            st.subheader("Worst Losses")
            BestLoss2 = best_wins(schedule, scores, teams, RPI, SelectedTeam2, "Loss")
            st.dataframe(BestLoss2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

        st.subheader("Conference Games")
        CG2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Conf")
        st.dataframe(CG2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("OOC Tournament")
        OOC2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "OOC_Tourney")
        st.dataframe(OOC2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Tip-Off Tournament")
        TOT2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Tip-Off_Tourney")
        st.dataframe(TOT2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Mascot Challenge")
        M2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Mascot")
        st.dataframe(M2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Luck of the Draw")
        LOTD2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Luck")
        st.dataframe(LOTD2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Cross-Conference Showdown")
        CC2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Cross_Conf")
        st.dataframe(CC2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Best of the Best")
        BOB2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Best_Of_Best")
        st.dataframe(BOB2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Rivalry Week")
        R2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Rivalry")
        st.dataframe(R2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Regional Rights")
        RR2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Regional")
        st.dataframe(RR2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Conference Tournament")
        CT2 = get_team_schedule(schedule, scores, teams, SelectedTeam2, "Conf_Tourney")
        st.dataframe(CT2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

    with col3:
        SelectedTeam3 = st.selectbox("Select Team 3", options=teams["Team"].tolist(), index=teams["Team"].tolist().index("Boston College"))
        st.image(get_logo(teams, SelectedTeam3))

        col9, col10 = st.columns([1,1])
        with col9:
            st.metric(label = "Total Record", value = get_team_stat(base_records, SelectedTeam3, "Record"), delta = get_team_stat(base_records, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 2 Record", value = get_team_stat(Quad2, SelectedTeam3, "Record"), delta = get_team_stat(Quad2, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 3 Record", value = get_team_stat(Quad3, SelectedTeam3, "Record"), delta = get_team_stat(Quad3, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Ratings Power Index", value = get_team_stat(RPI, SelectedTeam3, "RPI"), delta = get_team_stat(RPI, SelectedTeam3, "RPI_Rk"), delta_color = "off", border = True)
            st.metric(label = "Points Per Week", value = get_team_stat(PPG, SelectedTeam3, "Avg Score"), delta = get_team_stat(PPG, SelectedTeam3, "PPG_Rk"), delta_color = "off", border = True)
            st.subheader("Best Wins")
            BestWins3 = best_wins(schedule, scores, teams, RPI, SelectedTeam3, "Win")
            st.dataframe(BestWins3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})        

        with col10:
            st.metric(label = "Conference Record", value = get_team_stat(conf_records, SelectedTeam3, "Record"), delta = get_team_stat(conf_records, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 1 Record", value = get_team_stat(Quad1, SelectedTeam3, "Record"), delta = get_team_stat(Quad1, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 4 Record", value = get_team_stat(Quad4, SelectedTeam3, "Record"), delta = get_team_stat(Quad4, SelectedTeam3, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Strength of Schedule", value = get_team_stat(RPI, SelectedTeam3, "SOS"), delta = get_team_stat(RPI, SelectedTeam3, "SOS_Rk"), delta_color = "off", border = True)
            st.metric(label = "Weighted Recent", value = get_team_stat(WPPG, SelectedTeam3, "Weighted"), delta = get_team_stat(WPPG, SelectedTeam3, "Weight_Rk"), delta_color = "off", border = True)
            st.subheader("Worst Losses")
            BestLoss3 = best_wins(schedule, scores, teams, RPI, SelectedTeam3, "Loss")
            st.dataframe(BestLoss3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

        st.subheader("Conference Games")
        CG3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Conf")
        st.dataframe(CG3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("OOC Tournament")
        OOC3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "OOC_Tourney")
        st.dataframe(OOC3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Tip-Off Tournament")
        TOT3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Tip-Off_Tourney")
        st.dataframe(TOT3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Mascot Challenge")
        M3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Mascot")
        st.dataframe(M3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Luck of the Draw")
        LOTD3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Luck")
        st.dataframe(LOTD3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Cross-Conference Showdown")
        CC3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Cross_Conf")
        st.dataframe(CC3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Best of the Best")
        BOB3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Best_Of_Best")
        st.dataframe(BOB3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Rivalry Week")
        R3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Rivalry")
        st.dataframe(R3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Regional Rights")
        RR3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Regional")
        st.dataframe(RR3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Conference Tournament")
        CT3 = get_team_schedule(schedule, scores, teams, SelectedTeam3, "Conf_Tourney")
        st.dataframe(CT3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

    with col4:
        SelectedTeam4 = st.selectbox("Select Team 4", options=teams["Team"].tolist(), index=teams["Team"].tolist().index("Arkansas State"))
        st.image(get_logo(teams, SelectedTeam4))

        col11, col12 = st.columns([1,1])
        with col11:
            st.metric(label = "Total Record", value = get_team_stat(base_records, SelectedTeam4, "Record"), delta = get_team_stat(base_records, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 2 Record", value = get_team_stat(Quad2, SelectedTeam4, "Record"), delta = get_team_stat(Quad2, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 3 Record", value = get_team_stat(Quad3, SelectedTeam4, "Record"), delta = get_team_stat(Quad3, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Ratings Power Index", value = get_team_stat(RPI, SelectedTeam4, "RPI"), delta = get_team_stat(RPI, SelectedTeam4, "RPI_Rk"), delta_color = "off", border = True)
            st.metric(label = "Points Per Week", value = get_team_stat(PPG, SelectedTeam4, "Avg Score"), delta = get_team_stat(PPG, SelectedTeam4, "PPG_Rk"), delta_color = "off", border = True)
            st.subheader("Best Wins")
            BestWins4 = best_wins(schedule, scores, teams, RPI, SelectedTeam4, "Win")
            st.dataframe(BestWins4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})        

        with col12:
            st.metric(label = "Conference Record", value = get_team_stat(conf_records, SelectedTeam4, "Record"), delta = get_team_stat(conf_records, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 1 Record", value = get_team_stat(Quad1, SelectedTeam4, "Record"), delta = get_team_stat(Quad1, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Quad 4 Record", value = get_team_stat(Quad4, SelectedTeam4, "Record"), delta = get_team_stat(Quad4, SelectedTeam4, "Rank"), delta_color = "off", border = True)
            st.metric(label = "Strength of Schedule", value = get_team_stat(RPI, SelectedTeam4, "SOS"), delta = get_team_stat(RPI, SelectedTeam4, "SOS_Rk"), delta_color = "off", border = True)
            st.metric(label = "Weighted Recent", value = get_team_stat(WPPG, SelectedTeam4, "Weighted"), delta = get_team_stat(WPPG, SelectedTeam4, "Weight_Rk"), delta_color = "off", border = True)
            st.subheader("Worst Losses")
            BestLoss4 = best_wins(schedule, scores, teams, RPI, SelectedTeam4, "Loss")
            st.dataframe(BestLoss4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

        st.subheader("Conference Games")
        CG4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Conf")
        st.dataframe(CG4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("OOC Tournament")
        OOC4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "OOC_Tourney")
        st.dataframe(OOC4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Tip-Off Tournament")
        TOT4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Tip-Off_Tourney")
        st.dataframe(TOT4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Mascot Challenge")
        M4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Mascot")
        st.dataframe(M4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Luck of the Draw")
        LOTD4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Luck")
        st.dataframe(LOTD4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Cross-Conference Showdown")
        CC4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Cross_Conf")
        st.dataframe(CC4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Best of the Best")
        BOB4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Best_Of_Best")
        st.dataframe(BOB4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Rivalry Week")
        R4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Rivalry")
        st.dataframe(R4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Regional Rights")
        RR4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Regional")
        st.dataframe(RR4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
        st.subheader("Conference Tournament")
        CT4 = get_team_schedule(schedule, scores, teams, SelectedTeam4, "Conf_Tourney")
        st.dataframe(CT4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})



    def img_to_base64(path: str) -> str:
        """Convert a local image file to a base64 data URI."""
        try:
            data = Path(path).read_bytes()
            ext = Path(path).suffix.lstrip(".").lower()
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(ext, "png")
            return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
        except Exception:
            # Return a transparent 1x1 pixel placeholder if file not found
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


    def render_scorebug(
        team_a: str,
        team_b: str,
        logo_a: str,
        logo_b: str,
        record_a: str,
        record_b: str,
        score_a: int,
        score_b: int,
        color_a: str = "#E8002D",
        color_b: str = "#1D428A",
    ):
        logo_a_src = img_to_base64(logo_a) if not logo_a.startswith("http") else logo_a
        logo_b_src = img_to_base64(logo_b) if not logo_b.startswith("http") else logo_b

        html = f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;800&family=Barlow:wght@400;500&display=swap" rel="stylesheet">

        <style>
        .scorebug-wrap {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 48px 24px;
            background: transparent;
        }}

        .scorebug {{
            position: relative;
            width: 420px;
            border-radius: 16px;
            overflow: hidden;
            font-family: 'Barlow Condensed', sans-serif;
            box-shadow:
            0 0 0 1px rgba(255,255,255,0.08),
            0 24px 64px rgba(0,0,0,0.6);
            background: #0d0d0f;
        }}

        /* ── Team rows ─────────────────────────────────── */
        .team-row {{
            position: relative;
            display: flex;
            align-items: center;
            padding: 0 20px;
            height: 72px;
            gap: 14px;
            overflow: hidden;
            z-index: 1;
        }}

        .team-row::before {{
            content: '';
            position: absolute;
            inset: 0;
            opacity: 0.12;
            pointer-events: none;
            transition: opacity 0.3s;
        }}
        .team-row:hover::before {{ opacity: 0.2; }}

        .row-a::before {{
            background: radial-gradient(ellipse at 30% 50%, {color_a} 0%, transparent 70%);
        }}
        .row-b::before {{
            background: radial-gradient(ellipse at 30% 50%, {color_b} 0%, transparent 70%);
        }}

        /* Glow bar at top / bottom */
        .team-row::after {{
            content: '';
            position: absolute;
            left: 0; right: 0;
            height: 2px;
            pointer-events: none;
        }}
        .row-a::after {{
            top: 0;
            background: linear-gradient(90deg, {color_a}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_a};
            animation: glowPulse 2.4s ease-in-out infinite;
        }}
        .row-b::after {{
            bottom: 0;
            background: linear-gradient(90deg, {color_b}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_b};
            animation: glowPulse 2.4s ease-in-out infinite 1.2s;
        }}

        @keyframes glowPulse {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0.45; }}
        }}

        /* Divider */
        .divider {{
            height: 1px;
            background: linear-gradient(90deg,
            transparent 0%,
            rgba(255,255,255,0.15) 20%,
            rgba(255,255,255,0.15) 80%,
            transparent 100%);
        }}

        /* Logo */
        .team-logo {{
            width: 44px;
            height: 44px;
            object-fit: contain;
            flex-shrink: 0;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.5));
            border-radius: 6px;
        }}

        /* Team info */
        .team-info {{
            flex: 1;
            min-width: 0;
        }}
        .team-name {{
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #ffffff;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .team-record {{
            font-family: 'Barlow', sans-serif;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.06em;
            color: rgba(255,255,255,0.45);
            margin-top: 3px;
            text-transform: uppercase;
        }}

        /* Score */
        .team-score {{
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #ffffff;
            min-width: 52px;
            text-align: right;
            line-height: 1;
            text-shadow: 0 0 24px rgba(255,255,255,0.18);
            transition: transform 0.15s ease;
        }}

        /* Accent stripe on the left */
        .accent-stripe {{
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 4px;
        }}
        .row-a .accent-stripe {{
            background: {color_a};
            box-shadow: 2px 0 12px 0 {color_a};
        }}
        .row-b .accent-stripe {{
            background: {color_b};
            box-shadow: 2px 0 12px 0 {color_b};
        }}
        </style>

        <div class="scorebug-wrap">
        <div class="scorebug">

            <!-- Team A -->
            <div class="team-row row-a">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_a_src}" alt="{team_a} logo" />
            <div class="team-info">
                <div class="team-name">{team_a}</div>
                <div class="team-record">{record_a}</div>
            </div>
            <div class="team-score">{score_a}</div>
            </div>

            <div class="divider"></div>

            <!-- Team B -->
            <div class="team-row row-b">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_b_src}" alt="{team_b} logo" />
            <div class="team-info">
                <div class="team-name">{team_b}</div>
                <div class="team-record">{record_b}</div>
            </div>
            <div class="team-score">{score_b}</div>
            </div>

        </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


    # ── Demo / Sidebar controls ──────────────────────────────────────────────────

    st.markdown("## 🏟️ Scorebug Builder")
    st.markdown("Adjust the inputs in the sidebar and watch the bug update live.")

    with st.sidebar:
        st.header("Team A")
        team_a   = st.text_input("Name",      "CELTICS",    key="na")
        logo_a   = st.text_input("Logo URL",  "https://upload.wikimedia.org/wikipedia/en/thumb/8/8f/Boston_Celtics.svg/240px-Boston_Celtics.svg.png", key="la")
        record_a = st.text_input("Record",    "64-18",      key="ra")
        score_a  = st.number_input("Score",   value=108,    key="sa", step=1)
        color_a  = st.color_picker("Color",   "#007A33",    key="ca")

        st.divider()

        st.header("Team B")
        team_b   = st.text_input("Name",      "WARRIORS",   key="nb")
        logo_b   = st.text_input("Logo URL",  "https://upload.wikimedia.org/wikipedia/en/thumb/0/01/Golden_State_Warriors_logo.svg/240px-Golden_State_Warriors_logo.svg.png", key="lb")
        record_b = st.text_input("Record",    "46-36",      key="rb")
        score_b  = st.number_input("Score",   value=97,     key="sb", step=1)
        color_b  = st.color_picker("Color",   "#1D428A",    key="cb")

    render_scorebug(
        team_a=team_a,   team_b=team_b,
        logo_a=logo_a,   logo_b=logo_b,
        record_a=record_a, record_b=record_b,
        score_a=int(score_a), score_b=int(score_b),
        color_a=color_a, color_b=color_b,
    )

    st.components.v1.html(
        """
        ---
        **Usage as a component in your own app:**
        ```python
        render_scorebug(
            team_a="CELTICS",  team_b="WARRIORS",
            logo_a="./celtics.png", logo_b="./warriors.png",
            record_a="64-18",  record_b="46-36",
            score_a=108,       score_b=97,
            color_a="#007A33", color_b="#1D428A",
        )
        ```
        Logos accept **local file paths** or **public URLs**.
        """,
        unsafe_allow_html=False,
    )