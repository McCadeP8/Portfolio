import pandas as pd
import streamlit as st

st.set_page_config(
    page_title = "Data View",
    page_icon = ":bar_chart",
    layout = "wide")

st.title("CSV Data Viewer")

col1, col2 = st.columns([3, 2])
with col1:
    st.header("Vegas Blackjack")
    st.header(":bar_chart: Data from Google Sheets CSV Export")
    st.caption("Author: @McCadeP8")
with col2:
    st.image("https://pbs.twimg.com/media/Fxam4dlaIAIKnBb?format=png&name=4096x4096", width=200)



with st.sidebar:
    st.header("Filters")
    st.divider()

    Teams = ['Albuquerque', 'Anaheim', 'Anchorage', 'Austin', 'Baltimore', 'Birmingham', 'Boise', 'Buffalo', 'Cincinnati', 'Columbus', 'Des Moines', 'El Paso', 'Honolulu', 'Jacksonville', 'Kentucky', 'Lansing', 'Lincoln', 'Little Rock', 'Manchester', 'Nashville', 'Pittsburgh', 'Providence', 'San Diego', 'San Jose', 'Seattle', 'St. Louis', 'Tampa Bay', 'Tulsa', 'Vancouver', 'Vegas']
    SelectedTeam = st.selectbox("Select Your Team:", Teams, index=Teams.index("Vegas"))

team_colors = {
    "Albuquerque": {"bg": "#D72C2C", "text": "white"},
    "Anaheim": {"bg": "#DA0F10", "text": "white"},
    "Anchorage": {"bg": "#454B55", "text": "white"},
    "Austin": {"bg": "#040404", "text": "white"},
    "Baltimore": {"bg": "#00CED1", "text": "black"},
    "Birmingham": {"bg": "#853500", "text": "white"},
    "Boise": {"bg": "#744529", "text": "white"},
    "Buffalo": {"bg": "#152238", "text": "white"},
    "Cincinnati": {"bg": "#FFEA61", "text": "black"},
    "Columbus": {"bg": "#CD7F32", "text": "white"},
    "Des Moines": {"bg": "#1B1E23", "text": "white"},
    "El Paso": {"bg": "#F8EFAE", "text": "black"},
    "Honolulu": {"bg": "#CDC0C0", "text": "black"},
    "Jacksonville": {"bg": "#36454F", "text": "white"},
    "Kentucky": {"bg": "#663399", "text": "white"},
    "Lansing": {"bg": "#B9EFE1", "text": "black"},
    "Lincoln": {"bg": "#FC6A03", "text": "black"},
    "Little Rock": {"bg": "#710193", "text": "white"},
    "Manchester": {"bg": "#D7F2FA", "text": "black"},
    "Nashville": {"bg": "#450012", "text": "white"},
    "Pittsburgh": {"bg": "#F1F137", "text": "black"},
    "Providence": {"bg": "#BF0A30", "text": "white"},
    "San Diego": {"bg": "#31439B", "text": "white"},
    "San Jose": {"bg": "#97EBF4", "text": "black"},
    "Seattle": {"bg": "#006241", "text": "white"},
    "St. Louis": {"bg": "#B7B1AE", "text": "black"},
    "Tampa Bay": {"bg": "#FC8EAC", "text": "black"},
    "Tulsa": {"bg": "#333333", "text": "white"},
    "Vancouver": {"bg": "#17780D", "text": "black"},
    "Vegas": {"bg": "#35654D", "text": "white"},
}

bg_color = team_colors[SelectedTeam]["bg"]
text_color = team_colors[SelectedTeam]["text"]

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True)


@st.cache_data(ttl=120)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

df = get_data()

st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label = "Salary Cap", value = 154647000, delta = "10.0%", delta_color = "normal", help = "Salary Cap for the 2025-26 Season", border = True, format = "dollar")
with col2:
    st.metric(label = "Luxury Tax", value = 187895000, delta = "10.0%", delta_color = "normal", help = "Luxury Tax for the 2025-26 Season", border = True, format = "dollar")
with col3:
    st.metric(label = "Apron #1", value = 195945000, delta = "10.0%", delta_color = "normal", help = "First Apron for the 2025-26 Season", border = True, format = "dollar")
with col4:
    st.metric(label = "Apron #2", value = 207824000, delta = "10.0%", delta_color = "normal", help = "Second Apron for the 2025-26 Season", border = True, format = "dollar")

st.divider()

col1, col2 = st.columns([1, 4])
with col1:
    st.metric(label = "Cap Total", value = 244489135, delta = -89842135, delta_color = "normal", help = "Salary Cap Hit and Cap Space", border = True, format = "dollar")
    st.divider()
    st.header(":heavy_dollar_sign: Tax Space")
    st.text("-$23,022,997")
    st.divider()




with col2:
    st.header(f"{SelectedTeam} Cap Sheet for 2025-26 Season")
    if SelectedTeam:
        df = df[df["Team"] == SelectedTeam]
    else:
        df = df.copy()

    st.dataframe(df, use_container_width=True)