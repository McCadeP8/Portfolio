import streamlit as st
import re as re
from functions import get_data, get_pictures, active_players, style_salaries, overseas_players, free_agent_players, dead_players, draft_retired_players, active_player_n, inactive_player_n, get_exceptions, exception_table
from data import team_info, type_colors

df = get_data()
pics = get_pictures()
exceptions = get_exceptions()

with st.sidebar:
    Teams = ['Albuquerque', 'Anaheim', 'Anchorage', 'Austin', 'Baltimore', 'Birmingham', 'Boise', 'Buffalo', 'Cincinnati', 'Columbus', 'Des Moines', 'El Paso', 'Honolulu', 'Jacksonville', 'Kentucky', 'Lansing', 'Lincoln', 'Little Rock', 'Manchester', 'Nashville', 'Pittsburgh', 'Providence', 'San Diego', 'San Jose', 'Seattle', 'St. Louis', 'Tampa Bay', 'Tulsa', 'Vancouver', 'Vegas']
    SelectedTeam = st.selectbox("Select Your Team:", Teams, index=Teams.index("Vegas"))

bg_color = team_info[SelectedTeam]["bg"]
text_color = team_info[SelectedTeam]["text"]
team_logo = team_info[SelectedTeam]["logo"]
nickname = team_info[SelectedTeam]["nickname"]

#st.markdown(
#    f"""
#    <style>
#    .stApp {{
#        background-color: {bg_color};
#        color: {text_color};
#    }}
#    </style>
#    """,
#    unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .stApp {{
        background-color: black;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True)


st.set_page_config(
    page_title = "SBC Cap Sheets",
    page_icon = ":basketball:",
    layout = "wide")


col1, col2 = st.columns([4, 1])
with col1:
    st.title(":basketball::trophy: SBC Fantasy Basketball League:trophy::basketball:")
    st.header(f"{SelectedTeam} {nickname}")
with col2:
    st.image(team_logo, width=250)

st.divider()

tab1, tab2 = st.tabs([f"{SelectedTeam} Cap Sheet", "League Overview"])

with tab1:

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label = "Salary Cap", value = 154647000, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    with col2:
        st.metric(label = "Luxury Tax", value = 187895000, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    with col3:
        st.metric(label = "Apron #1", value = 195945000, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    with col4:
        st.metric(label = "Apron #2", value = 207824000, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

    st.header(f"{SelectedTeam} Cap Sheet for 2025-26 Season")
    if SelectedTeam:
        df = df[df["Team"] == SelectedTeam]
    else:
        df = df.copy()

    col1, col2 = st.columns([1, 4])

    with col1:
        st.divider()

        st.markdown("""
            **Cap Sheet Legend:** \n
            <span style="background-color:#FCE5CD;padding:6px 20px;border-radius:5px;">&nbsp;</span> Guaranteed \n 
            <span style="background-color:#F4CCCC;padding:6px 20px;border-radius:5px;">&nbsp;</span> Non-Guaranteed \n
            <span style="background-color:#CFE2F3;padding:6px 20px;border-radius:5px;">&nbsp;</span> Team Option \n
            <span style="background-color:#D9D2E9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Unrestricted \n
            <span style="background-color:#CFFFFF;padding:6px 20px;border-radius:5px;">&nbsp;</span> Restricted \n
            <span style="background-color:#D9D9D9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Dead \n
            """, unsafe_allow_html=True)

        st.divider()

        st.metric(label = "Players", value = active_player_n(df, SelectedTeam), delta = inactive_player_n(df, SelectedTeam), delta_color = "off", help = "The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border = True, format = "plain", delta_arrow = "off")
        st.metric(label = "Cap Total", value = 244489135, delta = -89842135, delta_color = "normal", help = "The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border = True, format = "dollar")
        st.metric(label = "Tax Total", value = 210917997, delta = -23022997, delta_color = "normal", help = "The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border = True, format = "dollar")
        st.metric(label = "Apron Space", value = "Uncapped", delta = None, help = "The first value shows how far the team is from the applicable cap, while the second indicates whether the team is uncapped, capped at the first apron, or capped at the second apron.", border = True, format = "dollar")
        st.metric(label = "Entry Fee", value = 73.31, delta = 20.39, delta_color = "inverse", help = "The league uses a 3,000,000‑1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border = True, format = "dollar")
        st.metric(label = "Net Fee", value = 0.00, delta = 93.31, delta_color = "normal", help = "The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border = True, format = "dollar")

    with col2:

        st.subheader("Active Players")
        active_player_df = active_players(df, pics, SelectedTeam)
        active_player_df = (active_player_df.style
            .apply(lambda row: style_salaries(row, type_colors), axis=1)  
            .format({c: "${:,.0f}" for c in active_player_df.columns if re.match(r"\d{4}", c)}))
        st.dataframe(active_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player", "2026", "2027", "2028", "2029", "2030","2031", "2032", "Bird Rights"), column_config={" ": st.column_config.ImageColumn(" ")})

        overseas_player_df = overseas_players(df, pics, SelectedTeam)
        if overseas_player_df.shape[0] > 0:
            st.subheader("Overseas Players")
            overseas_player_df = (overseas_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in overseas_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(overseas_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player", "2026", "2027", "2028", "2029", "2030","2031", "2032", "Bird Rights"), column_config={" ": st.column_config.ImageColumn(" ")})
        
        dead_player_df = dead_players(df, pics, SelectedTeam)
        if dead_player_df.shape[0] > 0:
            st.subheader("Dead Players")
            dead_player_df = (dead_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in dead_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player", "2026", "2027", "2028", "2029", "2030","2031", "2032"), column_config={" ": st.column_config.ImageColumn(" ")})

        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.subheader("Exceptions")
            exception_df = exception_table(exceptions, SelectedTeam)
            exception_df = (exception_df.style
              .format({"Amount": "${:,.0f}"}))
            st.dataframe(exception_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—")

        with col2:
            free_agent_player_df = free_agent_players(df, pics, SelectedTeam)
            if free_agent_player_df.shape[0] > 0:
                st.subheader("Free Agents")
                free_agent_player_df = (free_agent_player_df.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in free_agent_player_df.columns if re.match(r"\d{4}", c)}))
                st.dataframe(free_agent_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player", "2027"), column_config={" ": st.column_config.ImageColumn(" ")})

        with col3:
            draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
            if draft_retired_player_df.shape[0] > 0:
                st.subheader("Draft Rights & Retired")
                draft_retired_player_df = (draft_retired_player_df.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in draft_retired_player_df.columns if re.match(r"\d{4}", c)}))
                st.dataframe(draft_retired_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player"), column_config={" ": st.column_config.ImageColumn(" ")})



with tab2:
    st.markdown("This section is under construction.")