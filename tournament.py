import streamlit as st
from datetime import datetime, time
import random

# Page config
st.set_page_config(
    page_title="64-Team Tournament Bracket",
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
    
    /* Round Navigation */
    .round-nav {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin: 30px 0;
        flex-wrap: wrap;
    }
    
    .round-nav-btn {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        padding: 12px 25px;
        background: rgba(42, 42, 74, 0.6);
        border: 2px solid #2a2a4a;
        border-radius: 10px;
        color: #7a7a9a;
        cursor: pointer;
        transition: all 0.3s ease;
        letter-spacing: 2px;
    }
    
    .round-nav-btn:hover {
        border-color: #00ff88;
        color: #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        transform: translateY(-2px);
    }
    
    .round-nav-btn.active {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 212, 255, 0.2));
        border-color: #00ff88;
        color: #00ff88;
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.4);
    }
    
    /* Round Headers */
    .round-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.5rem;
        color: #00ff88;
        text-align: center;
        margin: 40px 0 30px 0;
        letter-spacing: 3px;
        text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
        position: relative;
    }
    
    .round-info {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #00d4ff;
        text-align: center;
        margin-top: 10px;
        opacity: 0.8;
    }
    
    /* Match Card */
    .match-card {
        background: rgba(26, 26, 46, 0.8);
        border: 2px solid #2a2a4a;
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
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
        transform: translateY(-3px);
        box-shadow: 0 15px 50px rgba(0, 255, 136, 0.3);
    }
    
    .match-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.9rem;
        color: #00d4ff;
        margin-bottom: 12px;
        letter-spacing: 1px;
        opacity: 0.7;
    }
    
    /* Team Row */
    .team-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        margin: 6px 0;
        border-radius: 10px;
        background: rgba(42, 42, 74, 0.5);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .team-row.winner {
        background: linear-gradient(90deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 255, 136, 0.05) 100%);
        border-color: #00ff88;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.25);
    }
    
    .team-row.loser {
        opacity: 0.5;
    }
    
    .team-info {
        display: flex;
        align-items: center;
        gap: 15px;
        flex: 1;
    }
    
    .team-seed {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.3rem;
        color: #00d4ff;
        min-width: 35px;
        text-align: center;
        opacity: 0.7;
    }
    
    .team-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .team-score {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.8rem;
        color: #00ff88;
        min-width: 50px;
        text-align: right;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    /* Bracket View */
    .bracket-container {
        display: flex;
        gap: 40px;
        padding: 20px;
        overflow-x: auto;
        min-height: 600px;
    }
    
    .bracket-round {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        min-width: 280px;
        gap: 20px;
    }
    
    .bracket-match {
        background: rgba(26, 26, 46, 0.9);
        border: 2px solid #2a2a4a;
        border-radius: 12px;
        padding: 12px;
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
        align-items: center;
        padding: 10px 12px;
        margin: 4px 0;
        background: rgba(42, 42, 74, 0.4);
        border-radius: 8px;
        border-left: 3px solid transparent;
    }
    
    .bracket-team.winner {
        border-left-color: #00ff88;
        background: rgba(0, 255, 136, 0.15);
    }
    
    .bracket-team-info {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .bracket-seed {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem;
        color: #00d4ff;
        min-width: 25px;
        opacity: 0.7;
    }
    
    .bracket-team-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    .bracket-team-score {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.4rem;
        color: #00ff88;
        text-shadow: 0 0 8px rgba(0, 255, 136, 0.4);
    }
    
    .bracket-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.3rem;
        color: #00d4ff;
        text-align: center;
        margin-bottom: 15px;
        letter-spacing: 2px;
        padding: 10px;
        background: rgba(0, 212, 255, 0.1);
        border-radius: 8px;
        border: 1px solid rgba(0, 212, 255, 0.3);
    }
    
    .champion-badge {
        text-align: center;
        margin: 30px auto;
        padding: 20px;
        max-width: 400px;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 165, 0, 0.2));
        border: 3px solid #ffd700;
        border-radius: 15px;
        box-shadow: 0 0 40px rgba(255, 215, 0, 0.5);
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 40px rgba(255, 215, 0, 0.5); }
        50% { box-shadow: 0 0 60px rgba(255, 215, 0, 0.8); }
    }
    
    .champion-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        color: #ffd700;
        letter-spacing: 3px;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
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
    
    /* Navigation arrows */
    .nav-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 30px;
        margin: 30px 0;
    }
    
    .nav-arrow {
        font-size: 2rem;
        color: #00ff88;
        cursor: pointer;
        transition: all 0.3s ease;
        user-select: none;
    }
    
    .nav-arrow:hover {
        transform: scale(1.2);
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
    }
    
    .nav-arrow.disabled {
        color: #2a2a4a;
        cursor: not-allowed;
    }
    
    .current-round-display {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        color: #00ff88;
        letter-spacing: 3px;
        min-width: 300px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Team names generator
def generate_team_names():
    cities = [
        "Phoenix", "Thunder", "Warriors", "Rockets", "Lakers", "Celtics", "Heat", "Bulls",
        "Mavericks", "Nets", "Blazers", "Raptors", "Nuggets", "Clippers", "Spurs", "Kings",
        "Hawks", "Hornets", "Jazz", "Wizards", "Pistons", "Magic", "Pacers", "Cavaliers",
        "Pelicans", "Timberwolves", "Grizzlies", "Bucks", "76ers", "Knicks", "Suns", "Wolves",
        "Dragons", "Tigers", "Lions", "Eagles", "Falcons", "Ravens", "Panthers", "Jaguars",
        "Cobras", "Vipers", "Sharks", "Dolphins", "Whales", "Bears", "Cougars", "Lynx",
        "Storm", "Lightning", "Blaze", "Inferno", "Cyclones", "Hurricanes", "Tornadoes", "Typhoons",
        "Knights", "Titans", "Giants", "Spartans", "Gladiators", "Crusaders", "Samurai", "Vikings"
    ]
    return cities[:64]

# Generate match scores
def generate_score(is_winner):
    if is_winner:
        return random.randint(18, 25)
    else:
        return random.randint(10, 17)

# Initialize tournament data
def init_tournament_data():
    teams = generate_team_names()
    
    # Create seeded matchups (1 vs 64, 2 vs 63, etc.)
    tournament = {
        'teams': teams,
        'rounds': []
    }
    
    # Round 1 - Round of 64
    round1_matches = []
    for i in range(32):
        seed1 = i + 1
        seed2 = 64 - i
        team1_wins = random.choice([True, False])
        
        match = {
            'match_number': i + 1,
            'teams': [
                {
                    'name': teams[seed1 - 1],
                    'seed': seed1,
                    'score': generate_score(team1_wins)
                },
                {
                    'name': teams[seed2 - 1],
                    'seed': seed2,
                    'score': generate_score(not team1_wins)
                }
            ]
        }
        round1_matches.append(match)
    
    tournament['rounds'].append({
        'name': 'Round of 64',
        'round_number': 1,
        'matches': round1_matches
    })
    
    # Generate subsequent rounds
    round_names = ['Round of 32', 'Sweet 16', 'Elite 8', 'Final Four', 'Championship']
    previous_winners = [match['teams'][0] if match['teams'][0]['score'] > match['teams'][1]['score'] 
                       else match['teams'][1] for match in round1_matches]
    
    for round_num, round_name in enumerate(round_names, 2):
        current_matches = []
        new_winners = []
        
        for i in range(0, len(previous_winners), 2):
            team1 = previous_winners[i]
            team2 = previous_winners[i + 1]
            team1_wins = random.choice([True, False])
            
            match = {
                'match_number': len(current_matches) + 1,
                'teams': [
                    {
                        'name': team1['name'],
                        'seed': team1['seed'],
                        'score': generate_score(team1_wins)
                    },
                    {
                        'name': team2['name'],
                        'seed': team2['seed'],
                        'score': generate_score(not team1_wins)
                    }
                ]
            }
            current_matches.append(match)
            
            winner = match['teams'][0] if team1_wins else match['teams'][1]
            new_winners.append(winner)
        
        tournament['rounds'].append({
            'name': round_name,
            'round_number': round_num,
            'matches': current_matches
        })
        
        previous_winners = new_winners
    
    return tournament

if 'tournament_data' not in st.session_state:
    st.session_state.tournament_data = init_tournament_data()
    st.session_state.current_round = 0

def render_match_card(match):
    """Render a match card with teams and scores"""
    team1, team2 = match['teams']
    winner_idx = 0 if team1['score'] > team2['score'] else 1
    
    html = f"""
    <div class="match-card">
        <div class="match-number">Match #{match['match_number']}</div>
    """
    
    for idx, team in enumerate(match['teams']):
        is_winner = idx == winner_idx
        winner_class = 'winner' if is_winner else 'loser'
        html += f"""
        <div class="team-row {winner_class}">
            <div class="team-info">
                <span class="team-seed">#{team['seed']}</span>
                <span class="team-name">{team['name']}</span>
            </div>
            <span class="team-score">{team['score']}</span>
        </div>
        """
    
    html += "</div>"
    return html

def render_bracket_match(match):
    """Render a bracket-style match"""
    team1, team2 = match['teams']
    winner_idx = 0 if team1['score'] > team2['score'] else 1
    
    html = '<div class="bracket-match">'
    
    for idx, team in enumerate([team1, team2]):
        is_winner = idx == winner_idx
        winner_class = 'winner' if is_winner else ''
        html += f"""
        <div class="bracket-team {winner_class}">
            <div class="bracket-team-info">
                <span class="bracket-seed">#{team['seed']}</span>
                <span class="bracket-team-name">{team['name']}</span>
            </div>
            <span class="bracket-team-score">{team['score']}</span>
        </div>
        """
    
    html += "</div>"
    return html

# Tournament Header
st.markdown("""
<div class="tournament-header">
    <div class="tournament-title">🏆 March Madness Style Tournament</div>
    <div class="tournament-subtitle">64 Team Single Elimination Championship</div>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["📋 Match View", "🏆 Bracket View"])

with tab1:
    # Round navigation
    rounds = st.session_state.tournament_data['rounds']
    
    # Navigation controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous Round", disabled=(st.session_state.current_round == 0), 
                    use_container_width=True):
            st.session_state.current_round -= 1
            st.rerun()
    
    with col2:
        current_round = rounds[st.session_state.current_round]
        st.markdown(f"""
        <div class="round-header">{current_round['name']}</div>
        <div class="round-info">{len(current_round['matches'])} matches</div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Round ➡️", disabled=(st.session_state.current_round == len(rounds) - 1),
                    use_container_width=True):
            st.session_state.current_round += 1
            st.rerun()
    
    # Display matches for current round
    matches = current_round['matches']
    
    # Determine column layout based on number of matches
    if len(matches) >= 16:
        cols = st.columns(4)
    elif len(matches) >= 8:
        cols = st.columns(3)
    elif len(matches) >= 4:
        cols = st.columns(2)
    else:
        cols = st.columns(1)
    
    for idx, match in enumerate(matches):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            st.markdown(render_match_card(match), unsafe_allow_html=True)
    
    # Show champion if on final round
    if st.session_state.current_round == len(rounds) - 1:
        final_match = matches[0]
        champion = final_match['teams'][0] if final_match['teams'][0]['score'] > final_match['teams'][1]['score'] else final_match['teams'][1]
        st.markdown(f"""
        <div class="champion-badge">
            <div class="champion-text">👑 Tournament Champion 👑<br>#{champion['seed']} {champion['name']}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div style="text-align: center; margin: 20px 0;"><div class="round-header" style="margin: 0;">Full Tournament Bracket</div></div>', 
               unsafe_allow_html=True)
    
    # Create scrollable bracket
    st.markdown('<div class="bracket-container">', unsafe_allow_html=True)
    
    bracket_html = '<div style="display: flex; gap: 40px; padding: 20px;">'
    
    for round_data in rounds:
        bracket_html += f'<div class="bracket-round">'
        bracket_html += f'<div class="bracket-label">{round_data["name"]}</div>'
        
        for match in round_data['matches']:
            bracket_html += render_bracket_match(match)
        
        bracket_html += '</div>'
    
    bracket_html += '</div>'
    
    st.markdown(bracket_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Champion display
    final_round = rounds[-1]
    final_match = final_round['matches'][0]
    champion = final_match['teams'][0] if final_match['teams'][0]['score'] > final_match['teams'][1]['score'] else final_match['teams'][1]
    
    st.markdown(f"""
    <div class="champion-badge">
        <div class="champion-text">👑 Tournament Champion 👑<br>#{champion['seed']} {champion['name']}</div>
    </div>
    """, unsafe_allow_html=True)

# Footer with stats
total_matches = sum(len(r['matches']) for r in rounds)
st.markdown(f'<div style="text-align: center; margin-top: 60px; padding: 20px; color: #7a7a9a; font-size: 0.9rem;">64 Teams • {total_matches} Total Matches • 6 Rounds • Built with Streamlit</div>', 
           unsafe_allow_html=True)
