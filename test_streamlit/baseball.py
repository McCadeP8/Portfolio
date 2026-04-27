import streamlit as st
from pybaseball import statcast
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Baseball Pitch Dashboard", layout="wide")
st.title("Baseball Pitch Analysis Dashboard")

with st.sidebar:
    st.header("Select Game")
    selected_date = st.date_input("Date", value=pd.Timestamp("2025-04-13"))

date_str = selected_date.strftime("%Y-%m-%d")

with st.spinner("Loading games..."):
    df = statcast(start_dt=date_str, end_dt=date_str)

if df.empty:
    st.warning("No games found for this date.")
else:
    games = df.sort_values("at_bat_number").groupby("game_pk").last().reset_index()
    games = games[["game_pk", "home_team", "away_team", "post_home_score", "post_away_score"]]
    
    game_choices = []
    for _, g in games.iterrows():
        label = f"{g['away_team']} @ {g['home_team']} ({int(g['post_away_score'])}-{int(g['post_home_score'])})"
        game_choices.append((g['game_pk'], label))
    
    with st.sidebar:
        game_idx = st.selectbox("Game", range(len(game_choices)), format_func=lambda i: game_choices[i][1])
        selected_pk = game_choices[game_idx][0]
    
    game_df = df[df['game_pk'] == selected_pk].copy()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Away", game_df['away_team'].iloc[0])
    with col2:
        away_score = int(game_df['post_away_score'].iloc[-1])
        home_score = int(game_df['post_home_score'].iloc[-1])
        st.metric("Final", f"{away_score}-{home_score}")
    with col3:
        st.metric("Home", game_df['home_team'].iloc[0])
    
    st.divider()
    
    t1, t2, t3, t4, t5 = st.tabs(["Pitch Map", "Types", "Outcomes", "Pitchers", "Game Flow"])
    
    with t1:
        st.subheader("Strike Zone Heat Map")
        plot_df = game_df.dropna(subset=['plate_x', 'plate_z'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_df['plate_x'], y=plot_df['plate_z'],
            mode='markers',
            marker=dict(size=7, color=plot_df['release_speed'], colorscale='Viridis', showscale=True, opacity=0.7, colorbar=dict(title="mph")),
            text=[f"{row['pitch_type']}<br>{row['release_speed']:.1f}mph<br>{row['description']}" for _, row in plot_df.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.add_shape(type="rect", x0=-0.83, y0=1.5, x1=0.83, y1=3.5, line=dict(color="red", width=2), fillcolor="rgba(0,0,0,0)")
        
        fig.update_layout(title="Pitcher Perspective", xaxis_title="Horizontal (ft)", yaxis_title="Vertical (ft)", height=600)
        st.plotly_chart(fig, use_container_width=True)
    
    with t2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Pitch Mix")
            counts = game_df['pitch_type'].value_counts()
            st.plotly_chart(px.pie(values=counts.values, names=counts.index), use_container_width=True)
        
        with col2:
            st.subheader("Velocity Distribution")
            v_df = game_df.dropna(subset=['pitch_type', 'release_speed'])
            st.plotly_chart(px.box(v_df, x='pitch_type', y='release_speed', title=""), use_container_width=True)
    
    with t3:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Pitch Results")
            desc = game_df['description'].value_counts().head(10)
            st.plotly_chart(px.bar(y=desc.index, x=desc.values, orientation='h'), use_container_width=True)
        
        with col2:
            st.subheader("Strike/Ball")
            sb = game_df['type'].value_counts()
            labels = ['Strike' if x == 'S' else 'Ball' if x == 'B' else x for x in sb.index]
            st.plotly_chart(px.pie(values=sb.values, names=labels), use_container_width=True)
    
    with t4:
        st.subheader("Pitcher Stats")
        p_stats = game_df.groupby('pitcher').agg({'pitch_type': 'count', 'release_speed': 'mean', 'type': lambda x: (x == 'S').sum()})
        p_stats.columns = ['Pitches', 'Avg Vel', 'Strikes']
        p_stats['Strike %'] = (p_stats['Strikes'] / p_stats['Pitches'] * 100).round(1)
        st.dataframe(p_stats, use_container_width=True)
    
    with t5:
        st.subheader("Score by Inning")
        flow = game_df[['inning', 'post_home_score', 'post_away_score']].drop_duplicates().sort_values('inning')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=flow['inning'], y=flow['post_away_score'], mode='lines+markers', name=game_df['away_team'].iloc[0]))
        fig.add_trace(go.Scatter(x=flow['inning'], y=flow['post_home_score'], mode='lines+markers', name=game_df['home_team'].iloc[0]))
        fig.update_layout(xaxis_title="Inning", yaxis_title="Score", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Pitches", len(game_df))
        col2.metric("Home Runs", len(game_df[game_df['events'] == 'home_run']))
        col3.metric("Strikeouts", len(game_df[game_df['events'] == 'strikeout']))
        col4.metric("Walks", len(game_df[game_df['events'].isin(['walk', 'intent_walk'])]))
