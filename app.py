import streamlit as st
import requests
from datetime import datetime
import pytz

# --- 1. CONFIG ---
st.set_page_config(page_title="Masters Leaderboard", layout="wide", page_icon="⛳")

TEAMS = {
    "Andy": ["Bryson DeChambeau", "Cameron Young", "Justin Rose", "Hideki Matsuyama", "Collin Morikawa", "Patrick Reed"],
    "Trevor": ["Jon Rahm", "Xander Schauffele", "Tommy Fleetwood", "Brooks Koepka", "Jordan Spieth", "Chris Gotterup"],
    "Ronan": ["Rory McIlroy", "Ludvig Åberg", "Matt Fitzpatrick", "Robert MacIntyre", "Viktor Hovland", "Shane Lowry"]
}

# --- 2. STYLING (GRID REMOVED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    :root {
        --masters-green: #004a23;
        --masters-gold: #ffce00;
        --score-under: #2e7d32;
        --score-over: #d32f2f;
        --bg-gray: #f4f5f7;
    }

    .stAppViewMain > div:nth-child(1) { padding-top: 0 !important; }
    .stApp { background-color: var(--bg-gray); }

    .header-outer {
        background-color: var(--masters-green);
        color: white;
        margin: -6rem -6rem 3rem -6rem;
        border-bottom: 6px solid var(--masters-gold);
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 300px; text-align: center;
    }
    
    .m-title { font-family: 'Libre Baskerville', serif; font-size: 4.5rem; margin: 0; line-height: 1; letter-spacing: -2px; }
    .last-updated-box { font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 3px; color: rgba(255,255,255,0.8); margin-top: 25px; }

    .t-card { background: white; border-radius: 12px; padding: 2.2rem 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border-top: 6px solid var(--masters-green); text-align: center; margin-bottom: 2rem; }
    .t-owner { font-size: 1.8rem; font-weight: 900; color: #111; text-transform: uppercase; letter-spacing: 1px; }
    .t-score { font-size: 4.8rem; font-weight: 900; color: var(--masters-green); margin-top: 10px; letter-spacing: -3px; }

    .table-container { background: white; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.04); margin-bottom: 3.5rem; overflow: hidden; border: 1px solid #e5e7eb; }
    .table-head { background: var(--masters-green); color: white; padding: 1.5rem 2.5rem; font-family: 'Libre Baskerville', serif; font-size: 1.7rem; text-align: center; }
    
    .m-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
    
    /* 1. Remove Vertical Grid Lines from Headers */
    .m-table th { 
        background: #f9fafb; 
        color: #111827; 
        font-size: 1.1rem; 
        text-transform: uppercase; 
        padding: 22px 10px; 
        text-align: center; 
        border-bottom: 2px solid #edf2f7; 
        font-weight: 800; 
        border-right: none !important; /* Forces no vertical line */
    }
    
    /* 2. Remove Vertical Grid Lines from Cells */
    .m-table td { 
        padding: 22px 10px; 
        border-bottom: 1px solid #f3f4f6; 
        font-size: 1.05rem; 
        text-align: center; 
        border-right: none !important; /* Forces no vertical line */
    }
    
    /* 3. Center columns (Today, status, R1-R4) but left-align player name */
    .m-table th:first-child, 
    .m-table td:first-child { 
        text-align: left !important; 
        padding-left: 25px !important; 
    }
    
    .p-name { font-weight: 700; color: #111827; font-size: 1.15rem; }
    .score-under { color: var(--score-under); font-weight: 800; }
    .score-over { color: var(--score-over) !important; font-weight: 800; }
    .score-par { color: #111827; font-weight: 800; }
    .delta-text { font-size: 0.9rem; margin-left: 4px; font-weight: 700; }
    
    .badge { padding: 6px 14px; border-radius: 6px; font-size: 0.9rem; font-weight: 700; background: #f3f4f6; color: #374151; }
    .tee-time { color: #b45309; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 3. LIVE DATA CONNECTION (STAYS) ---
@st.cache_data(ttl=60)
def get_live_masters_data():
    url = "https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?event=401581079"
    try:
        resp = requests.get(url).json()
        competitors = resp['competitions'][0]['competitors']
        data_map = {}
        
        for c in competitors:
            name = c['athlete']['displayName']
            # Rounds and scores
            rounds = [r.get('value', 0) for r in c.get('linescores', [])]
            scores = {f"r{i+1}": str(rounds[i]) for i in range(len(rounds))}
            
            # Logic for tee time vs live thru
            status_obj = c['status']
            display_status = status_obj.get('type', {}).get('detail', '-')
            
            # Determine state
            state = 'in'
            if status_obj.get('type', {}).get('state') == 'pre':
                state = 'pre'
            elif status_obj.get('type', {}).get('state') == 'post' or "final" in display_status.lower():
                state = 'post'
                display_status = "Final"

            data_map[name] = {
                "today": c.get('score', {}).get('value', 0),
                "thru": status_obj.get('thru', display_status),
                "state": state,
                "r1": scores.get('r1', '-'),
                "r2": scores.get('r2', '-'),
                "r3": scores.get('r3', '-'),
                "r4": scores.get('r4', '-'),
                "tee": display_status
            }
        return data_map
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        return {}

# --- 4. CALCULATION & HELPERS ---
def format_round_score(score_str):
    if score_str in ["-", "0", "None"]: return "-"
    try:
        score = int(score_str)
        delta = score - 72
        if delta < 0: return f"{score} <span class='score-under delta-text'>({delta})</span>"
        if delta > 0: return f"{score} <span class='score-over delta-text'>(+{delta})</span>"
        return f"{score} <span class='score-par delta-text'>(E)</span>"
    except: return "-"

def get_score_meta(val):
    try:
        n = int(val)
        return ("score-under", f"{n:+}") if n < 0 else (("score-over", f"{n:+}") if n > 0 else ("score-par", "E"))
    except: return "score-par", "E"

def calculate_best_4(team_players):
    total_delta = 0
    for r_key in ['r1', 'r2', 'r3', 'r4']:
        deltas = []
        for p in team_players:
            val = p.get(r_key)
            if val and val != "-":
                deltas.append(int(val) - 72)
            elif p['state'] == 'in' and any(tp.get(r_key) != "-" for tp in team_players):
                deltas.append(0)
        
        if deltas:
            deltas.sort()
            while len(deltas) < 4: deltas.append(0)
            deltas.sort()
            total_delta += sum(deltas[:4])
    return total_delta

# --- 5. EXECUTION ---
master_db = get_live_masters_data()
team_summaries = []

for owner, roster in TEAMS.items():
    processed = []
    for p_name in roster:
        p_data = master_db.get(p_name)
        if not p_data: # Match name automatically (McIlroy vs Mcllroy)
            p_data = next((v for k, v in master_db.items() if p_name in k or k in p_name), None)
            
        raw = p_data or {"today": 0, "state": "pre", "thru": "-", "r1": "-", "r2": "-", "r3": "-", "r4": "-", "tee": "TBD"}
        
        p_total = 0
        for r in ['r1', 'r2', 'r3', 'r4']:
            if raw[r] != "-": p_total += (int(raw[r]) - 72)

        processed.append(raw | {"name": p_name, "p_total": p_total})
    
    team_summaries.append({
        "owner": owner,
        "total": calculate_best_4(processed),
        "players": sorted(processed, key=lambda x: x['p_total'])
    })

team_summaries.sort(key=lambda x: x['total'])

# --- 6. RENDER ---
pst_now = datetime.now(pytz.timezone('US/Pacific')).strftime("%I:%M %p PST")
st.markdown(f'<div class="header-outer"><div class="m-title">The Masters</div><div class="last-updated-box">Live Updates • {pst_now}</div></div>', unsafe_allow_html=True)

cols = st.columns(3)
for i, team in enumerate(team_summaries):
    style, txt = get_score_meta(team['total'])
    with cols[i]:
        st.markdown(f'<div class="t-card"><div class="t-owner">{team["owner"]}</div><div class="t-score {style}">{txt}</div></div>', unsafe_allow_html=True)

for team in team_summaries:
    rows = ""
    for p in team['players']:
        t_style, t_txt = get_score_meta(p['today'])
        tot_style, tot_txt = get_score_meta(p['p_total'])
        status = f"<span class='tee-time'>{p['thru']}</span>" if p['state'] == 'pre' else f"<span class='badge'>{p['thru']}</span>"
        
        # Center columns (Today, status, R1-R4) but left-align player name
        rows += f"<tr><td class='p-name'>{p['name']}</td><td class='{t_style}'>{t_txt}</td><td>{status}</td><td>{format_round_score(p['r1'])}</td><td>{format_round_score(p['r2'])}</td><td>{format_round_score(p['r3'])}</td><td>{format_round_score(p['r4'])}</td><td class='{tot_style}'>{tot_txt}</td></tr>"
    
    # We remove the width on the columns so they size naturally, except Player which is wide
    st.markdown(f'<div class="table-container"><div class="table-head">{team["owner"]}\'s Roster</div><table class="m-table"><thead><tr><th style="width:28%">Player</th><th>Today</th><th>Status/Tee</th><th>R1</th><th>R2</th><th>R3</th><th>R4</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
