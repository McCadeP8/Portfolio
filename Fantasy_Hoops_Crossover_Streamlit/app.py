import streamlit as st
import re as re
from data import get_weekly_scores, get_schedule, get_teams, get_logo, get_team_schedule

st.set_page_config(
    page_title = "Fantasy Hoops Crossover",
    page_icon = ":basketball:",
    layout = "wide")

teams = get_teams()
schedule = get_schedule()
scores = get_weekly_scores()

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    SelectedTeam1 = st.selectbox("Select Team 1", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam1))
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
    R1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Rivarly")
    st.dataframe(R1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
    st.subheader("Regional Rights")
    RR1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Regional")
    st.dataframe(RR1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})
    st.subheader("Conference Tournament")
    CT1 = get_team_schedule(schedule, scores, teams, SelectedTeam1, "Conf_Tourney")
    st.dataframe(CT1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn("Opponent")})

with col2:
    SelectedTeam2 = st.selectbox("Select Team 2", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam2))

with col3:
    SelectedTeam3 = st.selectbox("Select Team 3", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam3))

with col4:
    SelectedTeam4 = st.selectbox("Select Team 4", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam4))
