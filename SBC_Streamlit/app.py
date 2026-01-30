import streamlit as st
import re as re
from functions import get_data, get_pictures, active_players, style_salaries, overseas_players, free_agent_players, dead_players, draft_retired_players, active_player_n, inactive_player_n, get_exceptions, exception_table, get_cap_total, get_tax_total, get_base_cap, team_hard_cap, team_hard_cap_n, base_fee, amount_paid, net_fee, luxury_fee, trade_restrictions, active_players_all, inactive_players_all, dead_players_all, draft_rights_all, retired_all, all_free_agents, trade_restrictions_all, overall_cap_table, unit_payout, tax_payout_champ, tax_payout_split, style_overall_cap, get_draft_picks, full_draft_picks, swap_draft_picks, split_draft_picks
from data import team_info, type_colors, current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, current_year, columns_order, year_offset
from trade_machine import tradeable_players_in, tradeable_players_out, tradeable_picks_in, tradeable_picks_out, players_out_table, players_in_table

df = get_data()
pics = get_pictures()
exceptions = get_exceptions()
base_cap = get_base_cap()
dp = get_draft_picks()

with st.sidebar:
    Teams = sorted(team_info.keys())
    SelectedTeam = st.selectbox("Select Your Team:", Teams, index=Teams.index("Vegas"))
    bg_color = team_info[SelectedTeam]["bg"]
    text_color = team_info[SelectedTeam]["text"]
    text_color2 = team_info[SelectedTeam]["bg2"]
    team_logo = team_info[SelectedTeam]["logo"]
    nickname = team_info[SelectedTeam]["nickname"]
    st.image(team_logo, width=250)

st.markdown(
    f"""
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {{
        background-color: {bg_color};
    }}

    /* Sidebar text */
    section[data-testid="stSidebar"] * {{
        color: {text_color2} !important;
    }}

    /* Selectbox container */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: {bg_color} !important;
        border: 1px solid "{bg_color}" !important;
    }}

    /* Selected value text */
    section[data-testid="stSidebar"] span {{
        color: {text_color2} !important;
    }}

    /* Dropdown menu */
    div[data-baseweb="popover"] {{
        background-color: {text_color2} !important;
    }}

    /* Dropdown options */
    div[data-baseweb="menu"] {{
        background-color: {text_color2} !important;
    }}

    /* Hovered option */
    div[data-baseweb="option"]:hover {{
        background-color: rgba(255,255,255,0.15) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(
    page_title = "SBC Cap Sheets",
    page_icon = ":basketball:",
    layout = "wide")


col1, col2 = st.columns([4, 1])
with col1:
    st.title(":basketball::trophy: SBC Fantasy Basketball League:trophy::basketball:")

st.divider()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([f"{SelectedTeam} Cap Sheet", f"{SelectedTeam} Draft Picks", "All Players", "All Draft Picks", "SBCFBL Overview", "Trade Machine", "About SBCFBL", "Data Checks"])

with tab1:
    st.header(f"{SelectedTeam} Cap Sheet for {current_year-1}-{str(current_year)[-2:]} Season")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

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
            <span style="background-color:#D9D9D9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Dead
            """, unsafe_allow_html=True)

        st.metric(label = "Players", value = active_player_n(df, SelectedTeam), delta = inactive_player_n(df, SelectedTeam), delta_color = "off", help = "The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border = True, format = "plain", delta_arrow = "off")
        st.metric(label = "Cap Total", value = get_cap_total(df, exceptions, SelectedTeam), delta = get_cap_total(df, exceptions, SelectedTeam)-current_salary_cap, delta_color = "inverse", help = "The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border = True, format = "dollar")
        st.metric(label = "Tax Total", value = get_tax_total(df, SelectedTeam), delta = get_tax_total(df, SelectedTeam)-current_luxury_tax, delta_color = "inverse", help = "The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border = True, format = "dollar")
        st.metric(label = "Apron Space", value = team_hard_cap(base_cap, SelectedTeam), delta = team_hard_cap_n(df, SelectedTeam, base_cap), help = "The first value indicates whether the team is uncapped, capped at the first apron, or capped at the second apron while the second value shows how far the team is from the applicable cap ", border = True, format = "dollar")
        st.metric(label = "Entry Fee", value = base_fee(df, SelectedTeam, base_cap), delta = luxury_fee(df, SelectedTeam, base_cap), delta_color = "inverse", help = "The SBCFBL uses a 3,000,000‑1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border = True, format = "dollar")
        st.metric(label = "Balance", value = net_fee(df, SelectedTeam, base_cap), delta = amount_paid(base_cap, SelectedTeam), delta_color = "normal", help = "The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border = True, format = "dollar")

    with col2:

        st.subheader("Active Players")
        active_player_df = active_players(df, pics, SelectedTeam)
        active_player_df = (active_player_df.style
            .apply(lambda row: style_salaries(row, type_colors), axis=1)  
            .format({c: "${:,.0f}" for c in active_player_df.columns if re.match(r"\d{4}", c)}))
        st.dataframe(active_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})

        overseas_player_df = overseas_players(df, pics, SelectedTeam)
        if overseas_player_df.shape[0] > 0:
            st.subheader("Overseas Players")
            overseas_player_df = (overseas_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in overseas_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(overseas_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})
        
        dead_player_df = dead_players(df, pics, SelectedTeam)
        if dead_player_df.shape[0] > 0:
            st.subheader("Dead Players")
            dead_player_df = (dead_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in dead_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(" ")})

    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        st.subheader("Exceptions")
        exception_df = exception_table(exceptions, SelectedTeam)
        exception_df = (exception_df.style
            .format({"Amount": "${:,.0f}"}))
        st.dataframe(exception_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—")

    with col2:
        free_agent_player_df = free_agent_players(df, pics, SelectedTeam)
        if free_agent_player_df.shape[0] > 0:
            st.subheader("Upcoming Free Agents")
            free_agent_player_df = (free_agent_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in free_agent_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(free_agent_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + [str(current_year+ year_offset)], column_config={" ": st.column_config.ImageColumn(" ")})

    with col3:
        restricted_df = trade_restrictions(df, pics, SelectedTeam)
        if restricted_df.shape[0] > 0:
            st.subheader("Trade Restrictions")
            st.dataframe(restricted_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={" ": st.column_config.ImageColumn(" ")})

    with col4:
        draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
        if draft_retired_player_df.shape[0] > 0:
            st.subheader("Draft Rights & Retired")
            draft_retired_player_df = (draft_retired_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in draft_retired_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(draft_retired_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player"), column_config={" ": st.column_config.ImageColumn(" ")})

with tab2:
    st.header(f"{SelectedTeam} Future Draft Picks")
    st.divider()
    st.header("Fully Owned Picks")
    st.dataframe(full_draft_picks(dp, SelectedTeam), width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})
    st.header("Swaped Draft Picks")
    st.dataframe(swap_draft_picks(dp, SelectedTeam), width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})
    st.header("Split Draft Picks")
    st.dataframe(split_draft_picks(dp, SelectedTeam), width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small")})








with tab3:

    col1, col2 = st.columns([1,7])

    with col1:

        st.markdown("""
            **Cap Sheet Legend:** \n
            <span style="background-color:#FCE5CD;padding:6px 20px;border-radius:5px;">&nbsp;</span> Guaranteed \n 
            <span style="background-color:#F4CCCC;padding:6px 20px;border-radius:5px;">&nbsp;</span> Non-Guaranteed \n
            <span style="background-color:#CFE2F3;padding:6px 20px;border-radius:5px;">&nbsp;</span> Team Option \n
            <span style="background-color:#D9D2E9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Unrestricted \n
            <span style="background-color:#CFFFFF;padding:6px 20px;border-radius:5px;">&nbsp;</span> Restricted \n
            <span style="background-color:#D9D9D9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Dead
            """, unsafe_allow_html=True)

    with col2:
        active_all_df = active_players_all(df, pics)
        if active_all_df.shape[0] > 0:
            st.subheader("Active Players")
            active_all_df = (active_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in active_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(active_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

        inactive_all_df = inactive_players_all(df, pics)
        if inactive_all_df.shape[0] > 0:
            st.subheader("Overseas Players")
            inactive_all_df = (inactive_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in inactive_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(inactive_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

        dead_players_df = dead_players_all(df, pics)
        if dead_players_df.shape[0] > 0:
            st.subheader("Dead Players")
            dead_players_df = (dead_players_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in dead_players_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_players_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    col1, col2, col3, col4 = st.columns([3,2,2,3])

    with col1:
        all_free_agents_df = all_free_agents(df, pics)
        if all_free_agents_df.shape[0] > 0:
            st.subheader("Upcoming Free Agents")
            all_free_agents_df = (all_free_agents_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in all_free_agents_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(all_free_agents_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + [str(current_year+ year_offset)], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col2:
        draft_all_df = draft_rights_all(df, pics)
        if draft_all_df.shape[0] > 0:
            st.subheader("Draft Rights")
            draft_all_df = (draft_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in draft_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(draft_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col3:
        retired_all_df = retired_all(df, pics)
        if retired_all_df.shape[0] > 0:
            st.subheader("Retired Rights")
            retired_all_df = (retired_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in retired_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(retired_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col4:
        trade_restrictins_all_df = trade_restrictions_all(df, pics)
        if trade_restrictins_all_df.shape[0] > 0:
            st.subheader("Trade Restrictions")
            trade_restrictins_all_df = (trade_restrictins_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in trade_restrictins_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(trade_restrictins_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player", "Trade Restriction"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

with tab4:
    st.markdown("This section is under construction.")

with tab5:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

    overall_cap_df = overall_cap_table(df, exceptions, base_cap)
    styled_overall_cap_df = (overall_cap_df.style
        .apply(lambda row: style_overall_cap(row), axis=1)
        .format({c: "${:,.2f}" for c in overall_cap_df.columns if c in ["Base Fee", "Luxury Fee", "Balance", "Amount Paid", "Cap Space", "Tax Space", "Apron 1 Space", "Apron 2 Space"]}))
    st.dataframe(styled_overall_cap_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="", width="small")})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label = "Champion Payout", value = unit_payout(df, exceptions, base_cap)*12, help = "Awarded to the SBCFBL Champion. Prize equals ½ of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Runner-Up Payout", value = unit_payout(df, exceptions, base_cap)*4, help = "Awarded to the SBCFBL Runner-up. Prize equals 1⁄6 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col3:
        st.metric(label = "Conference Finalists", value = unit_payout(df, exceptions, base_cap)*2, help = "Awarded to each Conference Runner-up (2 total). Prize equals 1⁄12 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col4:
        st.metric(label = "Conference Semifinalists", value = unit_payout(df, exceptions, base_cap)*1, help = "Awarded to each Conference Semifinal loser (4 total). Prize equals 1⁄24 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label = "Charity Champion", value = tax_payout_champ(df, exceptions, base_cap), help = "Awarded to the SBCFBL Champion to donate to a charity of their choice. Amount equals ½ of the luxury fee pool after all SBCFBL expenses.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Tax Payback", value = tax_payout_split(df, exceptions, base_cap), help = "Awarded to non-tax teams for finishing outside the tax. Amount equals ½ of the luxury fee pool after all SBCFBL expenses, split evenly among non-tax teams.", border = True, format = "dollar")

    with col3:
        st.metric(label = "IST Champion", value = 75, help = "Awarded to the SBCFBL Cup Champion. Prize is a flat $75.", border = True, format = "dollar")

    with col4:
        st.metric(label = "IST Runner Up", value = 15, help = "Awarded to the SBCFBL Cup Runner-up. Prize is a flat $15.", border = True, format = "dollar")

with tab6:

    with st.form("team_selection_form"):
        col1, col2 = st.columns(2)
        with col1:
            SelectedPlayersOut = st.multiselect("Outgoing Players:", tradeable_players_out(df, SelectedTeam))
            SelectedPicksOut = st.multiselect("Outgoing Picks:", tradeable_picks_out(dp, SelectedTeam))
        with col2:
            SelectedPlayersIn = st.multiselect("Incoming Players:", tradeable_players_in(df, SelectedTeam))
            SelectedPicksIn = st.multiselect("Incoming Picks:", tradeable_picks_in(dp, SelectedTeam))
        
        submitted = st.form_submit_button("Submit")

    if submitted:

        col1, col2 = st.columns(2)

        with col1:
            players_trade_out = players_out_table(df, pics, SelectedPlayersOut)
            if players_trade_out.shape[0] > 0:
                st.subheader("Players Going Out")
                players_trade_out = (players_trade_out.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in players_trade_out.columns if re.match(r"\d{4}", c)}))
                st.dataframe(players_trade_out, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(" ")})


        with col2:
            players_traded_in = players_in_table(df, pics, SelectedPlayersIn)
            if players_traded_in.shape[0] > 0:
                st.subheader("Players Coming In")
                players_traded_in = (players_traded_in.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in players_traded_in.columns if re.match(r"\d{4}", c)}))
                st.dataframe(players_traded_in, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    



































































with tab7:
    st.subheader("SBCFBL Introduction")
    st.markdown("""
    The **Sports Business Classroom Fantasy Basketball League (SBCFBL)** was established in Fall 2020 by alumni of the Sports Business Classroom 2019 and 2020 cohorts. The SBCFBL was inspired by guidance from Seth Partnow, who encouraged students pursuing careers in the NBA to gain hands-on experience by managing every aspect of a simulated professional team.

    The SBCFBL was created and developed from the ground up by [McCade Pearson](https://x.com/McCadeP8). Over the past six years, SBCFBL has been intentionally designed to closely mirror the structure, rules, and financial mechanics outlined in the NBA’s official [Collective Bargaining Agreement (CBA)](https://imgix.cosmicjs.com/25da5eb0-15eb-11ee-b5b3-fbd321202bdf-Final-2023-NBA-Collective-Bargaining-Agreement-6-28-23.pdf).

    Since its launch, SBCFBL has helped more than half a dozen participants secure roles with NBA teams and has raised over $10,000 for charitable causes, serving as both a professional development platform and a vehicle for positive community impact.
    """)

    st.divider()
    st.subheader("SBCFBL Pre-Launch")
    st.markdown("""
    During the SBCFBL's formation, McCade Pearson led the development of all franchise identities. This process included the creation of 30 distinct and original brands, each with a unique location, area-appropriate team name, and customized color scheme. In 2022, this branding effort was further expanded to include original team logos for every franchise.

    All 30 organizations are based in the United States or Vancouver. To date, the only franchise to undergo rebranding is the San Diego Wave, following the introduction of an NWSL expansion team with the same name.
    """)

    st.divider()
    st.subheader("SBCFBL Initial Roster Construction")
    st.markdown("""
    To initialize rosters, SBCFBL conducted a 30-team slow blind auction over the course of multiple 'days'. Each organization began with a clean salary cap sheet, along with access to the full Mid-Level Exception (MLE) and Bi-Annual Exception (BAE) in Year 1 to facilitate roster construction and competitive balance.

    To ensure a realistic distribution of contract lengths across the SBCFBL, contract values were permitted to differ from real-world figures, while contract durations were aligned with each player’s actual NBA contract length at the time. Following a series of randomized draws and strategic bidding rounds, all 30 team rosters were completed and the SBCFBL officially launched.
    """)

    st.divider()
    st.subheader("SBCFBL Scoring System")
    st.markdown("""
    The SBCFBL scoring system is modeled after the structure of the United States Electoral College. Rather than states, the SBCFBL allocates weighted values to traditional basketball performance categories that most strongly correlate with winning NBA games—beyond points alone.

    Each category contributes a fixed number of “votes,” with higher-impact metrics carrying greater weight.
    - **Points**: 61  
    - **Assists**: 41  
    - **True Shooting Percentage**: 41  
    - **Blocks**: 31  
    - **Defensive Rebounds**: 31  
    - **Offensive Rebounds**: 31  
    - **Plus-Minus**: 31  
    - **Steals**: 31  
    - **Three-Point Percentage**: 31  
    - **Two-Point Percentage**: 31  
    - **Free Throw Percentage**: -21  
    - **Turnovers***: 21
    - **Minutes Played**: 11  

    In total, **413 points** are available in each matchup, with **207 points required to win**. The inclusion of an additional digit in each category allows a tie to be resolved by awarding the win to the team that captures the most individual categories. In the rare event of a 206.5–206.5 tie, the win is awarded to the home team.

    To be eligible to win the four efficiency categories, teams must meet the following minimum thresholds: **10 field goal attempts (FGA)**, **10 three-point attempts (3PA)**, and **5 free throw attempts (FTA)**.

    This nontraditional scoring system expands strategic flexibility and encourages sophisticated analytical decision-making, creating a more dynamic and engaging competitive environment than standard fantasy formats.

    \**For Turnovers, the team with the lower total is awarded the category.*
    """)

    st.divider()
    st.subheader("SBCFBL Roster Construction")
    st.markdown("""
    To balance the need for a waiver wire, the SBCFBL employs unique roster rules. Each organization must maintain a **minimum of 12 players** and may carry **up to 14 players** during the season. Instead of two-way contracts, each organization has access to **three IR slots**. During the offseason, rosters may expand to a straight **17 players**.  

    The SBCFBL also accommodates **overseas players**. To qualify, a player must be drafted by the SBCFBL and assigned 'overseas' during the summer prior to the season, locking in their status on opening night. These players may remain overseas for the duration of their rookie contract. This system allows organizations to retain second-round draft picks in situations where a standard roster would not have space for them.

    On a day-to-day basis, each SBCFBL organization maintains roster spots for the following positions:

    - **Point Guard (PG)**  
    - **Shooting Guard (SG)**  
    - **Small Forward (SF)**  
    - **Power Forward (PF)**  
    - **Center (C)**  
    - **Three Flex (FLX)** 
    - **Six Bench**

    Player position eligibility is determined by **Fantrax** each season. Organizations may request the addition of a new position for a player within **two weeks after the season begins**. The commissioner reviews these requests using independent sources and makes the final decision.
    """)

    st.divider()
    st.subheader("SBCFBL Season Structure")
    st.markdown("""
    The SBCFBL consists of 30 organizations organized into six divisions across two conferences. The regular season schedule is designed to emulate the length and intensity of the NBA. Following minor adjustments due to COVID-shortened seasons, the SBCFBL now plays a **72-game schedule**, consisting of a **triple round-robin for 42 intraconference games** and a **double round-robin for 30 interconference games** per organization, spread over **36 periods**. Each period features two games per organization played over a 3–4 day stretch.

    The playoffs closely mirror the NBA’s format, beginning with **two rounds of three-day play-in games**, followed by **four rounds of seven-day playoff series**, ultimately producing a single, undisputed SBCFBL champion who hoists the Larry Coon Trophy.

    With the addition of the NBA Cup in 2023, the SBCFBL added a cup as well. organizations play four games in the five periods leading up to a quarterfinal, semfinal, and championship matchup that takes place over the NBA Cup Final. While NBA Cup Final games obviously don't count, they do in only our SBCFBL Cup Championship for entertainment purposes. None of the SBCFBL Cup games count towards our regular season standings due to the complexity of folding them into the regular season schedule. 
    """)

    st.divider()
    st.subheader("SBCFBL Financial Structure")
    st.markdown("""
    The SBCFBL initially launched using a **2,000,000:1 scale** relative to the NBA, meaning a player with a \$10,000,000 salary would cost an owner $5 in the league. As the NBA salary cap increased, the league adjusted to a **3,000,000:1 scale** for the 2025–26 season to keep entry fees accessible while maintaining realistic roster management. The league also enforces a **luxury tax** consistent with the NBA’s structure.

    Entry fees collected for each organization’s base roster are pooled into a league fund. These funds are first allocated to cover operational expenses, including **Fantrax fees** and the purchase of the **Larry Coon Trophy**. After these costs, remaining funds are distributed to successful organizations as follows:

    - **Champion**: 1/2 of the remaining pool  
    - **Runner-up**: 1/6 of the remaining pool  
    - **Conference Finalists (2 organizations)**: 1/12 each of the remaining poool
    - **Conference Semifinalists (4 organizations)**: 1/24 each each of the remaining pool

    In addition to entry fees, the SBCFBL collects **luxury tax payments**. During the league’s first five years, the full luxury tax pool was awarded to the league champion to donate to a charity of their choice. This approach both supported charitable causes and limited organizations’ ability to recoup luxury tax payments to fund additional championships.  

    As of the 2025–26 season, **50\% of the luxury tax pool continues to be allocated to charitable causes**, while the remaining 50\% is redistributed evenly among organizations that did not exceed the luxury tax threshold.

     **SBCFBL Cup** carries an entry fee of **\$3** per organization. The winner of the Cup receives **\$75**, while the runner-up is awarded **\$15**.
    """)

    st.divider()
    st.subheader("SBCFBL Free Agency")
    st.markdown("""
    The SBCFBL Free Agency moratorium spans **seven “days”**, each lasting 48 hours, concluding on **July 1, 3, 5, 7, 9, 11, and 13**. During this period, organizations place bids through a **Qualtrics survey**, with a maximum of **20 bids per organization per day**.

    After each day, **signings are announced**, along with an updated list of free agents showing the number of bids received and the current highest bid for each player.  

    Players are released in **three tiers** based on their previous season’s salary. A player signs after either receiving **five bids** or having at least one bid for **two consecutive days** (signing on the third day). Players sign for the **highest year-one salary bid**, and organizations determine contract length **as part of their bid**, not after securing the signing.  

    All offseason contracts in the SBCFBL are **fully guaranteed**. **Player options** are not permitted, as allowing them would require every signing to include one. Similarly, **team options** are disallowed outside of rookie contracts, ensuring clarity and consistency in all agreements.
    
    Any players with remaining bids sign on the **seventh day**, marking the end of the moratorium.

    **Restricted free agent signings** have just under one day for the incumbent organization to match a bid. **Sign-and-trade deals** are permitted, provided the transaction is agreed upon by the conclusion of the moratorium.

    In the event of multiple organizations submitting identical bids for a player, the incumbent organization has a **50\% chance** to retain the player, while the remaining organizations split the other 50%. For **supermax-eligible players**, if the incumbent organization matches the supermax amount, they have a **75\% chance** to retain the player.

    This 48-hour bidding process continues throughout free agency, but activity generally slows significantly after the moratorium concludes. Once the SBCFBL season begins, **contracts become non-guaranteed**, and organizations may only execute signings on the **first day of a matchup**.
    """)

    st.divider()
    st.subheader("SBCFBL Draft")
    st.markdown("""
    The SBCFBL Draft follows the same structure as the NBA Draft, including **lottery procedures and tiebreakers**. Rather than using a traditional countdown timer for each pick, the draft operates on **scheduled timeslots**. For example, the **first overall pick** always occurs between **10:00 a.m. and 10:30 a.m. EDT** on the Saturday following the NBA Draft, with the **second pick** due at **11:00 a.m. EDT**, and so on.

    If all organizations submit their picks early, the next organization may proceed immediately. Should a team **miss their designated timeslot**, multiple organizations may be placed **on the clock simultaneously**. Any organization that is **over two hours late** will have their pick **autodrafted**, typically receiving the highest remaining NBA draft pick (e.g., the first pick would be autodrafted at 12:30 p.m. EDT, likely selecting the 5th overall player).

    The **second round** follows the same timeslot framework on **Sunday**, maintaining consistency and pace throughout the draft.
    """)

    st.divider()
    st.subheader("SBCFBL Other Information")
    st.markdown("""
    All other SBCFBL operations adhere as closely as possible to the **NBA Collective Bargaining Agreement (CBA)**, including, but not limited to, **salary cap rules, trade regulations, exceptions, and deadlines**. Most SBCFBL deadlines are set on a **24-hour delay** relative to the NBA, including the **waive-and-stretch deadline, player guarantee date, offseason signing and trade restrictions,** and the **trade deadline**.

    This document is intended as a **quick-reference guide** and is not an exhaustive rulebook. Its purpose is to provide key information and highlight why the SBCFBL is considered **the premier fantasy basketball experience**.
    """)

with tab8:
    st.header("Missing Pictures")
    st.header("Missing Salary Info")
    st.header("Stepien Rule Broken")
    st.header("Hard Cap Broken")
    st.header("Roster Count Broken")
    st.header("Fantrax vs. Cap Sheets Rosters")