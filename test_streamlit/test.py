import streamlit as st
from datetime import date


def render_scoreboard(
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    home_logo_url: str,
    away_logo_url: str,
    game_date: str = None,
    league: str = None,
    venue: str = None,
    quarter_scores: list[dict] = None,  # e.g. [{"Q1": (7,3)}, {"Q2": (14,10)}, ...]
    game_status: str = "FINAL",
    home_record: str = None,
    away_record: str = None,
    home_color: str = "#1a1a2e",
    away_color: str = "#16213e",
):
    """
    Renders a beautiful 5:2 ratio scoreboard at the top of a Streamlit article.

    Parameters:
    -----------
    home_team       : Full team name (e.g. "Los Angeles Lakers")
    away_team       : Full team name
    home_score      : Final score for home team
    away_score      : Final score for away team
    home_logo_url   : Direct URL to home team logo image
    away_logo_url   : Direct URL to away team logo image
    game_date       : Display date string (e.g. "March 4, 2026"). Defaults to today.
    league          : League / competition name (e.g. "NBA", "NFL", "Premier League")
    venue           : Stadium / arena name
    quarter_scores  : List of period dicts, e.g. [{"label":"Q1","home":7,"away":3}, ...]
    game_status     : Status string shown above score (default "FINAL")
    home_record     : Win-loss record string (e.g. "42-18")
    away_record     : Win-loss record string
    home_color      : Accent hex color for home team side
    away_color      : Accent hex color for away team side
    """

    if game_date is None:
        game_date = date.today().strftime("%B %-d, %Y")

    winner = "home" if home_score > away_score else "away" if away_score > home_score else "tie"

    # Build quarter/period table HTML
    period_html = ""
    if quarter_scores:
        headers = "".join(f"<th>{p['label']}</th>" for p in quarter_scores)
        home_cells = "".join(f"<td>{p['home']}</td>" for p in quarter_scores)
        away_cells = "".join(f"<td>{p['away']}</td>" for p in quarter_scores)
        period_html = f"""
        <div class="period-table-wrap">
          <table class="period-table">
            <thead>
              <tr>
                <th class="team-col">TEAM</th>
                {headers}
                <th class="final-col">T</th>
              </tr>
            </thead>
            <tbody>
              <tr class="{'winner-row' if winner == 'away' else ''}">
                <td class="team-col">{away_team.split()[-1].upper()}</td>
                {away_cells}
                <td class="final-col total">{away_score}</td>
              </tr>
              <tr class="{'winner-row' if winner == 'home' else ''}">
                <td class="team-col">{home_team.split()[-1].upper()}</td>
                {home_cells}
                <td class="final-col total">{home_score}</td>
              </tr>
            </tbody>
          </table>
        </div>
        """

    meta_items = []
    if league:
        meta_items.append(f'<span class="meta-chip">{league}</span>')
    if venue:
        meta_items.append(f'<span class="meta-chip venue">📍 {venue}</span>')
    meta_bar = f'<div class="meta-bar">{"".join(meta_items)}</div>' if meta_items else ""

    record_home = f'<span class="record">{home_record}</span>' if home_record else ""
    record_away = f'<span class="record">{away_record}</span>' if away_record else ""

    winner_badge_home = '<span class="winner-badge">▲ W</span>' if winner == "home" else ""
    winner_badge_away = '<span class="winner-badge">▲ W</span>' if winner == "away" else ""

    scoreboard_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
      .sb-root {{
        font-family: 'Barlow', sans-serif;
        background: #0a0a0f;
        border-radius: 16px;
        overflow: hidden;
        position: relative;
        box-shadow:
          0 0 0 1px rgba(255,255,255,0.06),
          0 32px 80px rgba(0,0,0,0.7),
          0 8px 24px rgba(0,0,0,0.5);
        margin-bottom: 8px;
        aspect-ratio: 5 / 2;
        display: flex;
        flex-direction: column;
      }}

      /* ── animated grain overlay ── */
      .sb-root::before {{
        content: '';
        position: absolute;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
        opacity: 0.35;
        pointer-events: none;
        z-index: 10;
        border-radius: 16px;
      }}

      /* ── split background glow ── */
      .sb-glow-left {{
        position: absolute;
        left: -10%;
        top: -30%;
        width: 55%;
        height: 160%;
        background: radial-gradient(ellipse at 30% 50%, {home_color}99 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(2px);
      }}
      .sb-glow-right {{
        position: absolute;
        right: -10%;
        top: -30%;
        width: 55%;
        height: 160%;
        background: radial-gradient(ellipse at 70% 50%, {away_color}99 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(2px);
      }}

      /* ── top bar ── */
      .sb-topbar {{
        position: relative;
        z-index: 5;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 20px 6px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
      }}
      .sb-topbar .date-label {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.4);
      }}
      .sb-topbar .status-pill {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #f0c040;
        background: rgba(240,192,64,0.12);
        border: 1px solid rgba(240,192,64,0.3);
        padding: 3px 12px;
        border-radius: 50px;
      }}

      /* ── main score area ── */
      .sb-main {{
        position: relative;
        z-index: 5;
        flex: 1;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        padding: 0 24px;
        gap: 0;
      }}

      /* team block */
      .sb-team {{
        display: flex;
        align-items: center;
        gap: 18px;
      }}
      .sb-team.home {{ flex-direction: row; }}
      .sb-team.away {{ flex-direction: row-reverse; }}

      .team-logo-wrap {{
        position: relative;
        flex-shrink: 0;
      }}
      .team-logo-wrap img {{
        width: 88px;
        height: 88px;
        object-fit: contain;
        display: block;
        filter: drop-shadow(0 4px 20px rgba(0,0,0,0.6));
        transition: transform 0.3s ease;
      }}
      .team-logo-wrap img:hover {{
        transform: scale(1.05);
      }}

      .team-info {{ line-height: 1.2; }}
      .sb-team.away .team-info {{ text-align: right; }}

      .team-city {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.45);
        display: block;
      }}
      .team-name {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #ffffff;
        display: block;
        line-height: 1;
      }}
      .record {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1.5px;
        color: rgba(255,255,255,0.3);
        display: block;
        margin-top: 3px;
      }}
      .winner-badge {{
        display: inline-block;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #f0c040;
        border: 1px solid rgba(240,192,64,0.4);
        padding: 1px 6px;
        border-radius: 4px;
        margin-top: 4px;
      }}

      /* ── center score ── */
      .sb-center {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 0 20px;
      }}
      .score-row {{
        display: flex;
        align-items: center;
        gap: 0;
      }}
      .score-num {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 90px;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
        letter-spacing: -2px;
        text-shadow: 0 0 60px rgba(255,255,255,0.1);
      }}
      .score-num.winner-score {{
        color: #f0c040;
        text-shadow: 0 0 40px rgba(240,192,64,0.3);
      }}
      .score-divider {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 50px;
        font-weight: 300;
        color: rgba(255,255,255,0.2);
        padding: 0 8px;
        line-height: 1;
        margin-top: -8px;
      }}
      .vs-line {{
        width: 60px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      }}

      /* ── bottom bar ── */
      .sb-bottombar {{
        position: relative;
        z-index: 5;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px 20px 10px;
        border-top: 1px solid rgba(255,255,255,0.07);
        gap: 12px;
      }}

      /* meta bar */
      .meta-bar {{
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .meta-chip {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.4);
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 3px 10px;
        border-radius: 4px;
      }}
      .meta-chip.venue {{ letter-spacing: 1px; }}

      /* period table */
      .period-table-wrap {{
        overflow-x: auto;
        margin-top: 0;
      }}
      .period-table {{
        border-collapse: collapse;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        color: rgba(255,255,255,0.5);
        letter-spacing: 1px;
      }}
      .period-table th, .period-table td {{
        padding: 3px 10px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.07);
      }}
      .period-table th {{
        font-weight: 700;
        color: rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.03);
        letter-spacing: 2px;
        font-size: 10px;
      }}
      .period-table .team-col {{
        text-align: left;
        padding-left: 12px;
        font-weight: 700;
        color: rgba(255,255,255,0.6);
      }}
      .period-table .final-col {{
        font-weight: 700;
        color: rgba(255,255,255,0.6);
      }}
      .period-table .total {{
        color: #ffffff;
        font-size: 14px;
        font-weight: 900;
      }}
      .period-table .winner-row td {{
        color: rgba(255,255,255,0.7);
      }}
      .period-table .winner-row .total {{
        color: #f0c040;
      }}
    </style>

    <div class="sb-root">
      <div class="sb-glow-left"></div>
      <div class="sb-glow-right"></div>

      <!-- Top bar -->
      <div class="sb-topbar">
        <span class="date-label">{game_date}</span>
        <span class="status-pill">{game_status}</span>
        <span class="date-label" style="opacity:0">{game_date}</span>
      </div>

      <!-- Main score area -->
      <div class="sb-main">

        <!-- Home team (left) -->
        <div class="sb-team home">
          <div class="team-logo-wrap">
            <img src="{home_logo_url}" alt="{home_team}" onerror="this.style.opacity='0.3'"/>
          </div>
          <div class="team-info">
            <span class="team-city">{" ".join(home_team.split()[:-1]) or home_team}</span>
            <span class="team-name">{home_team.split()[-1]}</span>
            {record_home}
            {winner_badge_home}
          </div>
        </div>

        <!-- Center score -->
        <div class="sb-center">
          <div class="score-row">
            <span class="score-num {'winner-score' if winner == 'home' else ''}">{home_score}</span>
            <span class="score-divider">—</span>
            <span class="score-num {'winner-score' if winner == 'away' else ''}">{away_score}</span>
          </div>
          <div class="vs-line"></div>
        </div>

        <!-- Away team (right) -->
        <div class="sb-team away">
          <div class="team-logo-wrap">
            <img src="{away_logo_url}" alt="{away_team}" onerror="this.style.opacity='0.3'"/>
          </div>
          <div class="team-info">
            <span class="team-city">{" ".join(away_team.split()[:-1]) or away_team}</span>
            <span class="team-name">{away_team.split()[-1]}</span>
            {record_away}
            {winner_badge_away}
          </div>
        </div>

      </div>

      <!-- Bottom bar -->
      <div class="sb-bottombar">
        {meta_bar}
        {period_html}
      </div>
    </div>
    """

    st.html(scoreboard_html)


# ─────────────────────────────────────────────
# Demo / dev preview  (streamlit run scoreboard.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Scoreboard Demo")

    st.markdown(
        """
        <style>
          .stApp { background: #111117; }
          section[data-testid="stAppViewContainer"] { padding: 2rem 3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── NFL Example ──────────────────────────
    st.subheader("NFL Example", anchor=False)
    render_scoreboard(
        home_team="San Francisco 49ers",
        away_team="Kansas City Chiefs",
        home_score=22,
        away_score=25,
        home_logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/San_Francisco_49ers_logo.svg/1200px-San_Francisco_49ers_logo.svg.png",
        away_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/e/e1/Kansas_City_Chiefs_logo.svg/1200px-Kansas_City_Chiefs_logo.svg.png",
        game_date="February 11, 2024",
        league="NFL · Super Bowl LVIII",
        venue="Allegiant Stadium, Las Vegas",
        game_status="FINAL · OT",
        home_record="12-5",
        away_record="13-4",
        home_color="#AA0000",
        away_color="#E31837",
        quarter_scores=[
            {"label": "Q1", "home": 0, "away": 0},
            {"label": "Q2", "home": 10, "away": 13},
            {"label": "Q3", "home": 6, "away": 3},
            {"label": "Q4", "home": 6, "away": 6},
            {"label": "OT", "home": 0, "away": 3},
        ],
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── NBA Example ──────────────────────────
    st.subheader("NBA Example", anchor=False)
    render_scoreboard(
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        home_score=118,
        away_score=109,
        home_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/8f/Boston_Celtics.svg/1200px-Boston_Celtics.svg.png",
        away_logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Los_Angeles_Lakers_logo.svg/1200px-Los_Angeles_Lakers_logo.svg.png",
        game_date="March 4, 2026",
        league="NBA",
        venue="TD Garden, Boston",
        game_status="FINAL",
        home_record="48-14",
        away_record="35-27",
        home_color="#007A33",
        away_color="#552583",
        quarter_scores=[
            {"label": "Q1", "home": 31, "away": 28},
            {"label": "Q2", "home": 27, "away": 30},
            {"label": "Q3", "home": 33, "away": 24},
            {"label": "Q4", "home": 27, "away": 27},
        ],
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Soccer Example ──────────────────────────
    st.subheader("Soccer Example (no period scores)", anchor=False)
    render_scoreboard(
        home_team="Manchester City",
        away_team="Arsenal FC",
        home_score=2,
        away_score=2,
        home_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/1200px-Manchester_City_FC_badge.svg.png",
        away_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/1200px-Arsenal_FC.svg.png",
        game_date="March 31, 2024",
        league="Premier League · GW30",
        venue="Etihad Stadium, Manchester",
        game_status="FINAL",
        home_record="15W 5D 3L",
        away_record="16W 4D 3L",
        home_color="#6CABDD",
        away_color="#EF0107",
    )