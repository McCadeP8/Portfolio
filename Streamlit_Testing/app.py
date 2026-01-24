import streamlit as st
from functions import get_data, get_pictures, style_salaries
from data import team_colors

df = get_data()
pics = get_pictures()

with st.sidebar:
    st.header("Filters")
    st.divider()

    Teams = ['Albuquerque', 'Anaheim', 'Anchorage', 'Austin', 'Baltimore', 'Birmingham', 'Boise', 'Buffalo', 'Cincinnati', 'Columbus', 'Des Moines', 'El Paso', 'Honolulu', 'Jacksonville', 'Kentucky', 'Lansing', 'Lincoln', 'Little Rock', 'Manchester', 'Nashville', 'Pittsburgh', 'Providence', 'San Diego', 'San Jose', 'Seattle', 'St. Louis', 'Tampa Bay', 'Tulsa', 'Vancouver', 'Vegas']
    SelectedTeam = st.selectbox("Select Your Team:", Teams, index=Teams.index("Vegas"))


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
    st.metric(label = "Salary Cap", value = 154647000, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
with col2:
    st.metric(label = "Luxury Tax", value = 187895000, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
with col3:
    st.metric(label = "Apron #1", value = 195945000, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
with col4:
    st.metric(label = "Apron #2", value = 207824000, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

st.divider()

st.header(f"{SelectedTeam} Cap Sheet for 2025-26 Season")
if SelectedTeam:
    df = df[df["Team"] == SelectedTeam]
else:
    df = df.copy()

col1, col2 = st.columns([1, 4])

with col1:
    st.metric(label = "Players", value = 17, delta = 10, delta_color = "off", help = "The first number shows active roster players (up to 14, plus up to 3 inactive/IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border = True, format = "plain", delta_arrow = "off")
    st.metric(label = "Cap Total", value = 244489135, delta = -89842135, delta_color = "normal", help = "The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border = True, format = "dollar")
    st.metric(label = "Tax Total", value = 210917997, delta = -23022997, delta_color = "normal", help = "The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border = True, format = "dollar")
    st.metric(label = "Apron Space", value = "Uncapped", delta = None, help = "The first value shows how far the team is from the applicable cap, while the second indicates whether the team is uncapped, capped at the first apron, or capped at the second apron.", border = True, format = "dollar")
    st.metric(label = "Entry Fee", value = 73.31, delta = 20.39, delta_color = "inverse", help = "The league uses a 3,000,000‑1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border = True, format = "dollar")
    st.metric(label = "Net Fee", value = 0.00, delta = 93.31, delta_color = "normal", help = "The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border = True, format = "dollar")

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
    st.dataframe(styled_active, width = "stretch", height = "content", row_height = 100, hide_index=True, placeholder="—", column_order=("Picture_Online", "Player", "Y2026", "Y2027", "Y2028", "Y2029", "Y2030","Y2031", "Y2032"), column_config={"Picture_Online": st.column_config.ImageColumn("Picture_Online", width="medium")})
    if not inactive_df.empty:
        st.subheader("Non-Active Players")
        styled_inactive = (inactive_df.style
                          .apply(style_salaries, axis=1)
                          .format({c: "${:,.0f}" for c in inactive_df.columns if c.startswith("Y")}))
        st.dataframe(styled_inactive, width = "stretch", height = "content", hide_index=True, placeholder="—", column_order=("Picture_Online", "Player", "Y2026", "Y2027", "Y2028", "Y2029", "Y2030", "Y2031", "Y2032"), column_config={"Picture_Online": st.column_config.ImageColumn("Picture_Online", width="large")})