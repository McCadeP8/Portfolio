import pandas as pd
import streamlit as st

st.set_page_config(
    page_title = "Data View",
    page_icon = ":bar_chart",
    layout = "wide")

st.title("CSV Data Viewer")

st.header(":bar_chart: Data from Google Sheets CSV Export")
st.caption("Author: @McCadeP8")

with st.sidebar:
    st.header("Filters")
    st.divider()

    Teams = ['Albuquerque', 'Anaheim', 'Anchorage', 'Austin', 'Baltimore', 'Birmingham', 'Boise', 'Buffalo', 'Cincinnati', 'Columbus', 'Des Moines', 'El Paso', 'Honolulu', 'Jacksonville', 'Kentucky', 'Lansing', 'Lincoln', 'Little Rock', 'Manchester', 'Nashville', 'Pittsburgh', 'Providence', 'San Diego', 'San Jose', 'Seattle', 'St. Louis', 'Tampa Bay', 'Tulsa', 'Vancouver', 'Vegas']
    SelectedTeam = st.selectbox("Select Your Team:", Teams, index=Teams.index("Vegas"))

@st.cache_data(ttl=120)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

df = get_data()

col1, col2 = st.columns([1, 4])
with col1:
    st.text("Full DataFrame: 35,256")

with col2:
    st.header(f"{SelectedTeam} Cap Sheet for 2025-26 Season")
    if SelectedTeam:
        df = df[df["Team"].isin(SelectedTeam)]
    else:
        df = df.copy()

    st.dataframe(df, use_container_width=True)