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
    st.subheader("Tip-Off Tournament")
    st.subheader("Mascot Challenge")
    st.subheader("Luck of the Draw")
    st.subheader("Cross-Conference Showdown")
    st.subheader("Best of the Best")
    st.subheader("Rivalry Week")
    st.subheader("Conference Tournament")
    st.subheader("Regional Rights")


with col2:
    SelectedTeam2 = st.selectbox("Select Team 2", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam2))

with col3:
    SelectedTeam3 = st.selectbox("Select Team 3", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam3))

with col4:
    SelectedTeam4 = st.selectbox("Select Team 4", options=teams["Team"].tolist())
    st.image(get_logo(teams, SelectedTeam4))
