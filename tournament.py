import streamlit as st

# Page config
st.set_page_config(
    page_title="Tournament Bracket",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with bold aesthetic choices
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 2px;
        color: #00ff88 !important;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    p, div, span, label {
        font-family: 'DM Sans', sans-serif !important;
        color: #e0e0e0;
    }
    
    /* Tournament Header */
    .tournament-header {
        background: linear-gradient(90deg, rgba(0,255,136,0.1) 0%, rgba(0,212,255,0.1) 100%);
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 255, 136, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .tournament-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 4rem;
        color: #00ff88;
        text-shadow: 0 0 30px rgba(0, 255, 136, 0.8);
        margin: 0;
        letter-spacing: 4px;
    }
    
    .tournament-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.2rem;
        color: #00d4ff;
        margin-top: 10px;
    }
    
    /* Round Headers */
    .round-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        color: #00ff88;
        text-align: center;
        margin: 40px 0 20px 0;
        letter-spacing: 3px;
        text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
        position: relative;
    }
    
    .round-header:before,
    .round-header:after {
        content: '';
        position: absolute;
        top: 50%;
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ff88);
    }
    
    .round-header:before {
        right: 60%;
        background: linear-gradient(90deg, #00ff88, transparent);
    }
    
    .round-header:after {
        left: 60%;
    }
    
    /* Match Card */
    .match-card {
        background: rgba(26, 26, 46, 0.8);
        border: 2px solid #2a2a4a;
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .match-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .match-card:hover:before {
        left: 100%;
    }
    
    .match-card:hover {
        border-color: #00ff88;
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0, 255, 136, 0.3);
    }
    
    .court-info {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: #00d4ff;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(0, 212, 255, 0.3);
    }
    
    .court-name {
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    .match-time {
        font-weight: 500;
        opacity: 0.8;
    }
    
    /* Team Row */
    .team-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 20px;
        margin: 8px 0;
        border-radius: 12px;
        background: rgba(42, 42, 74, 0.5);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .team-row.winner {
        background: linear-gradient(90deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 255, 136, 0.05) 100%);
        border-color: #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    .team-row.loser {
        opacity: 0.6;
    }
    
    .team-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        flex: 1;
    }
    
    .team-score {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        color: #00ff88;
        min-width: 60px;
        text-align: right;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    /* Bracket View */
    .bracket-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 40px 20px;
        gap: 60px;
    }
    
    .bracket-round {
        display: flex;
        flex-direction: column;
        gap: 40px;
        min-width: 250px;
    }
    
    .bracket-match {
        background: rgba(26, 26, 46, 0.9);
        border: 2px solid #2a2a4a;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .bracket-match:hover {
        border-color: #00ff88;
        box-shadow: 0 12px 40px rgba(0, 255, 136, 0.3);
    }
    
    .bracket-team {
        display: flex;
        justify-content: space-between;
        padding: 12px 15px;
        margin: 5px 0;
        background: rgba(42, 42, 74, 0.4);
        border-radius: 8px;
        border-left: 3px solid transparent;
    }
    
    .bracket-team.winner {
        border-left-color: #00ff88;
        background: rgba(0, 255, 136, 0.15);
    }
    
    .bracket-team-name {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        color: #ffffff;
    }
    
    .bracket-team-score {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        color: #00ff88;
        text-shadow: 0 0 8px rgba(0, 255, 136, 0.4);
    }
    
    .bracket-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        color: #00d4ff;
        text-align: center;
        margin-bottom: 20px;
        letter-spacing: 2px;
    }
    
    .champion-badge {
        text-align: center;
        margin-top: 20px;
        padding: 15px;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 165, 0, 0.2));
        border: 2px solid #ffd700;
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.4);
    }
    
    .champion-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        color: #ffd700;
        letter-spacing: 2px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        letter-spacing: 2px;
        color: #7a7a9a;
        border-bottom: 3px solid transparent;
        padding: 15px 30px;
    }
    
    .stTabs [aria-selected="true"] {
        color: #00ff88;
        border-bottom-color: #00ff88;
        text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
    }
    
    /* Connector lines for bracket */
    .bracket-connector {
        width: 50px;
        height: 2px;
        background: linear-gradient(90deg, #2a2a4a, #00ff88);
        margin: 0 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize tournament data
if 'tournament_data' not in st.session_state:
    st.session_state.tournament_data = {
        'semifinals': [
            {
                'court': 'Court 1',
                'time': '13:00',
                'teams': [
                    {'name': 'Team 1', 'score': 21},
                    {'name': 'Team 4', 'score': 15}
                ]
            },
            {
                'court': 'Court 2',
                'time': '13:00',
                'teams': [
                    {'name': 'Team 2', 'score': 17},
                    {'name': 'Team 3', 'score': 21}
                ]
            }
        ],
        'final': {
            'court': 'Championship Court',
            'time': '15:00',
            'teams': [
                {'name': 'Team 1', 'score': 25},
                {'name': 'Team 3', 'score': 23}
            ]
        }
    }

def render_match_card(match, round_name="Semifinal"):
    """Render a match card with teams and scores"""
    team1, team2 = match['teams']
    winner_idx = 0 if team1['score'] > team2['score'] else 1
    
    html = f"""
    <div class="match-card">
        <div class="court-info">
            <span class="court-name">{match['court']}</span>
            <span class="match-time">🕐 {match['time']}</span>
        </div>
    """
    
    for idx, team in enumerate(match['teams']):
        is_winner = idx == winner_idx
        winner_class = 'winner' if is_winner else 'loser'
        html += f"""
        <div class="team-row {winner_class}">
            <span class="team-name">{team['name']}</span>
            <span class="team-score">{team['score']}</span>
        </div>
        """
    
    html += "</div>"
    return html

def render_bracket_match(teams, label=""):
    """Render a bracket-style match"""
    winner_idx = 0 if teams[0]['score'] > teams[1]['score'] else 1
    
    html = f"""
    <div>
        {f'<div class="bracket-label">{label}</div>' if label else ''}
        <div class="bracket-match">
    """
    
    for idx, team in enumerate(teams):
        is_winner = idx == winner_idx
        winner_class = 'winner' if is_winner else ''
        html += f"""
        <div class="bracket-team {winner_class}">
            <span class="bracket-team-name">{team['name']}</span>
            <span class="bracket-team-score">{team['score']}</span>
        </div>
        """
    
    html += "</div></div>"
    return html

# Tournament Header
st.markdown("""
<div class="tournament-header">
    <div class="tournament-title">🏆 Championship Tournament</div>
    <div class="tournament-subtitle">Four Team Single Elimination</div>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["📋 Match View", "🏆 Bracket View"])

with tab1:
    # Semifinals
    st.markdown('<div class="round-header">Semifinals</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(render_match_card(st.session_state.tournament_data['semifinals'][0], "Semifinal 1"), 
                   unsafe_allow_html=True)
    with col2:
        st.markdown(render_match_card(st.session_state.tournament_data['semifinals'][1], "Semifinal 2"), 
                   unsafe_allow_html=True)
    
    # Finals
    st.markdown('<div class="round-header">Championship Final</div>', unsafe_allow_html=True)
    
    # Center the final match
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(render_match_card(st.session_state.tournament_data['final'], "Final"), 
                   unsafe_allow_html=True)
        
        # Champion badge
        final_teams = st.session_state.tournament_data['final']['teams']
        champion = final_teams[0] if final_teams[0]['score'] > final_teams[1]['score'] else final_teams[1]
        st.markdown(f"""
        <div class="champion-badge">
            <div class="champion-text">👑 Champion: {champion['name']} 👑</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="bracket-label" style="font-size: 2rem; margin: 20px 0;">Tournament Bracket</div>', 
               unsafe_allow_html=True)
    
    # Create bracket layout
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown('<div class="bracket-label">Semifinals</div>', unsafe_allow_html=True)
        st.markdown(render_bracket_match(st.session_state.tournament_data['semifinals'][0]['teams'], "Match 1"), 
                   unsafe_allow_html=True)
        st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True)
        st.markdown(render_bracket_match(st.session_state.tournament_data['semifinals'][1]['teams'], "Match 2"), 
                   unsafe_allow_html=True)
    
    with col2:
        # Connector visualization
        st.markdown('<div style="height: 150px; display: flex; align-items: center; justify-content: center;"><div style="width: 100%; height: 3px; background: linear-gradient(90deg, #2a2a4a, #00ff88, #2a2a4a);"></div></div>', 
                   unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="bracket-label">Championship</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True)
        st.markdown(render_bracket_match(st.session_state.tournament_data['final']['teams'], "Final"), 
                   unsafe_allow_html=True)
        
        # Champion badge in bracket
        final_teams = st.session_state.tournament_data['final']['teams']
        champion = final_teams[0] if final_teams[0]['score'] > final_teams[1]['score'] else final_teams[1]
        st.markdown(f"""
        <div class="champion-badge">
            <div class="champion-text">👑 Tournament Champion<br>{champion['name']} 👑</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown('<div style="text-align: center; margin-top: 60px; padding: 20px; color: #7a7a9a; font-size: 0.9rem;">Built with Streamlit • Tournament Management System</div>', 
           unsafe_allow_html=True)