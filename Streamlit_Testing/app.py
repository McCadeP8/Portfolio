import pandas as pd
import streamlit as st
import re

@st.cache_data(ttl=120)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data(ttl=120)
def get_pictures() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1180190150"
    df = pd.read_csv(csv_url)
    df = df.drop(columns=["Picture"])
    return df

df = get_data()
pics = get_pictures()

type_colors = {
    "Guaranteed": "#FCE5CD",   
    "Non-Guaranteed": "#F4CCCC",
    "Team": "#CFE2F3",         
    "Dead": "#D9D9D9",         
    "Unrestricted": "#D9D2E9", 
    "Restricted": "#CFFFFF", 
}

def style_salaries(row):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        match = re.match(r"Y(\d{4})", col)
        if match:
            year = match.group(1)
            type_col = f"Type{year}"
            if type_col in row.index:
                contract_type = row[type_col]
                color = type_colors.get(contract_type, None)
                if color:
                    styles[i] = f"background-color: {color}; color: black;"
    return styles

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

st.set_page_config(
    page_title = "Data View",
    page_icon = ":bar_chart",
    layout = "wide")



col1, col2 = st.columns([4, 1])
with col1:
    st.title("CSV Data Viewer")
    st.header(":bar_chart: Data from Google Sheets CSV Export")
    st.caption("Author: @McCadeP8")
    st.header("Vegas Blackjack")
with col2:
    st.image("https://pbs.twimg.com/media/Fxam4dlaIAIKnBb?format=png&name=4096x4096", width=250)

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

st.header(f"{SelectedTeam} Cap Sheet for 2025-26 Season")
if SelectedTeam:
    df = df[df["Team"] == SelectedTeam]
else:
    df = df.copy()

col1, col2 = st.columns([1, 4])
with col1:
    st.metric(label = "Players", value = 17, delta = 10, delta_color = "off", help = "Number of Players on Active and Inactive Roster", border = True, format = "plain", delta_arrow = "off")
    st.metric(label = "Cap Total", value = 244489135, delta = -89842135, delta_color = "normal", help = "Salary Cap Hit and Cap Space", border = True, format = "dollar")
    st.metric(label = "Tax Total", value = 210917997, delta = -23022997, delta_color = "normal", help = "Tax Hit and Space", border = True, format = "dollar")
    st.metric(label = "Apron Space", value = None, help = "Tax Hit and Space", border = True, format = "dollar")
    st.metric(label = "Entry Fee", value = 73.31, delta = 20.39, delta_color = "inverse", help = "Entry Fee for Roster and Tax Fee", border = True, format = "dollar")
    st.metric(label = "Net Fee", value = 0.00, delta = 93.31, delta_color = "normal", help = "Currently Owed and Paid", border = True, format = "dollar")

with col2:
    df = df.merge(pics, on="Player", how="left")
    active_df = (df[df["Type"] == "Active Players"]
                .drop(columns=["Type", "Team", "Y2023", "Y2024", "Y2025", "Type2023", "Type2024", "Type2025", "Trade.Restriction"])
                .sort_values(by="Y2026", ascending=False))
    inactive_df = (df[df["Type"] == "Non-Active Players"]
                  .drop(columns=["Type", "Team", "Y2023", "Y2024", "Y2025", "Type2023", "Type2024", "Type2025", "Trade.Restriction"])
                  .sort_values(by="Y2026", ascending=False))
    st.subheader("Active Players")
    styled_active = (active_df.style
                    .apply(style_salaries, axis=1)
                    .format({c: "${:,.0f}" for c in active_df.columns if c.startswith("Y")}))
    st.dataframe(styled_active, width = "stretch", height = "content", hide_index=True, placeholder="—", column_order=("Picture_Online", "Player", "Y2026", "Y2027", "Y2028", "Y2029", "Y2030","Y2031", "Y2032"), column_config={"Picture_Online": st.column_config.ImageColumn("Picture_Online", width="small")}
)

    if not inactive_df.empty:
        st.subheader("Non-Active Players")
        styled_inactive = (inactive_df.style
                          .apply(style_salaries, axis=1)
                          .format({c: "${:,.0f}" for c in inactive_df.columns if c.startswith("Y")}))
        st.dataframe(styled_inactive, width = "stretch", height = "content", hide_index=True, placeholder="—", column_order=("Picture_Online", "Player", "Y2026", "Y2027", "Y2028", "Y2029", "Y2030", "Y2031", "Y2032"))

