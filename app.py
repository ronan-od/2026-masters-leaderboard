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

# --- 2. STYLING (FIXED FOR MOBILE SCROLLING) ---
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
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 250px; text-align: center;
    }
    
    .m-title { font-family: 'Libre Baskerville', serif; font-size: 3rem; margin: 0; line-height: 1; letter-spacing: -1px; }
    .last-updated-box { font-family: 'Inter', sans-serif; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: rgba(255,255,255,0.8); margin-top: 15px; }

    /* Team Cards */
    .t-card { background: white; border-radius: 12px; padding: 1.5rem 1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border-top: 6px solid var(--masters-green); text-align: center; margin-bottom: 1rem; }
    .t-owner { font-size: 1.2rem; font-weight: 900; color: #111; text-transform: uppercase; }
    .t-score { font-size: 3.5rem; font-weight: 900; color: var(--masters-green); margin-top: 5px; letter-spacing: -2px; }

    /* TABLE MOBILE FIX */
    .table-container { 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 4px 25px rgba(0,0,0,0.04); 
        margin-bottom: 2rem; 
        border: 1px solid #e5e7eb;
        overflow: hidden;
    }
    
    /* This wrapper enables horizontal scrolling on small screens */
    .responsive-table {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    .table-head { background: var(--masters-green); color: white; padding: 1rem; font-family: 'Libre Baskerville', serif; font-size: 1.4rem; text-align: center; }
    
    .m-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; min-width: 600px; } /* Ensures table doesn't squish too much */
    
    .m-table th { background: #f9fafb; color: #111827; font-size: 0.8rem; text-transform: uppercase; padding: 15px 8px; text-align: center; border-bottom: 2px solid #edf2f7; font-weight: 800; }
    .m-table td { padding: 15px 8px; border-bottom: 1px solid #f3f4f6; font-size: 0.9rem; text-align: center; }
    
    .m-table th:first-child, .m-table td:first-child { text-align: left !important; padding-left: 15px !important; position: sticky; left: 0; background: white; z-index: 1; }
    .m-table th:first-child { background: #f9fafb; }

    .p-name { font-weight: 700; color: #111827; }
    .score-under { color: var(--score-under); font-weight: 800; }
    .score-over { color: var(--score-over) !important; font-weight: 800; }
    .score-par { color: #111827; font-weight: 800; }
    .delta-text { font-size: 0.75rem; margin-left: 2px; font-weight: 700; }
    
    .badge { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; background: #f3f4f6; color: #374151; white-space: nowrap; }
    .tee-time { color: #b45309; font-weight: 700; font-size: 0.8rem; white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

# --- 3. LIVE DATA CONNECTION ---
@st.cache_data(ttl=60)
def get_live_masters_data():
    url = "https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?event=401811941"
    try:
        resp = requests.get(url).json()
        competitors = resp['events'][0]['competitions'][0]['competitors']
        data_map = {}
        for c in competitors:
            name = c['athlete']['displayName']
            scores = {}
            par_scores = {}
            for r in c.get('linescores', []):
                if 'value' in r:
                    period = r['period']
                    scores[f"r{period}"] = str(int(r['value']))
                    disp = r.get('displayValue', 'E')
                    try: par_scores[f"r{period}"] = 0 if disp == 'E' else int(disp.replace('+', ''))
                    except: par_scores[f"r{period}"] = 0
            status_obj = c['status']
            display_status = status_obj.get('type', {}).get('detail', '-')
            state = 'in'
            if status_obj.get('type', {}).get('state') == 'pre': state = 'pre'
            elif status_obj.get('type', {}).get('state') == 'post' or "final" in display_status.lower():
                state = 'post'
                display_status = "Final"
            score_display = c.get('score', {}).get('displayValue', 'E')
            if score_display == 'E':
                today_val = 0
            else:
                try: today_val = int(score_display.replace('+', ''))
                except: today_val = 0
            data_map[name] = {
                "today": today_val,
                "thru": status_obj.get('thru', display_status),
                "state": state,
                "r1": scores.get('r1', '-'), "r2": scores.get('r2', '-'), "r3": scores.get('r3', '-'), "r4": scores.get('r4', '-'),
                "r1_par": par_scores.get('r1'), "r2_par": par_scores.get('r2'), "r3_par": par_scores.get('r3'), "r4_par": par_scores.get('r4'),
                "tee": display_status
            }
        return data_map
    except: return {}

# --- 4. HELPERS ---
def format_round_score(score_str, par=None):
    if score_str in ["-", "0", "None"]: return "-"
    try:
        score = int(score_str)
        delta = par if par is not None else score - 72
        if delta < 0: return f"{score}<br><span class='score-under delta-text'>({delta})</span>"
        if delta > 0: return f"{score}<br><span class='score-over delta-text'>(+{delta})</span>"
        return f"{score}<br><span class='score-par delta-text'>(E)</span>"
    except: return "-"

def get_score_meta(val):
    try:
        n = int(val)
        return ("score-under", f"{n:+}") if n < 0 else (("score-over", f"{n:+}") if n > 0 else ("score-par", "E"))
    except: return "score-par", "E"

def calculate_best_4(team_players):
    total_delta = 0
    for r_key in ['r1', 'r2', 'r3', 'r4']:
        par_key = f"{r_key}_par"
        deltas = []
        for p in team_players:
            val = p.get(par_key)
            if val is not None: deltas.append(val)
            elif p['state'] == 'in' and any(tp.get(par_key) is not None for tp in team_players): deltas.append(0)
        if deltas:
            deltas.sort()
            while len(deltas) < 4: deltas.append(0)
            total_delta += sum(deltas[:4])
    return total_delta

# --- 5. EXECUTION ---
master_db = get_live_masters_data()
team_summaries = []

for owner, roster in TEAMS.items():
    processed = []
    for p_name in roster:
        p_data = master_db.get(p_name)
        if not p_data:
            p_data = next((v for k, v in master_db.items() if p_name in k or k in p_name), None)
        raw = p_data or {"today": 0, "state": "pre", "thru": "-", "r1": "-", "r2": "-", "r3": "-", "r4": "-", "tee": "TBD", "r1_par": None, "r2_par": None, "r3_par": None, "r4_par": None}
        p_total = sum(raw[f"r{i}_par"] for i in range(1, 5) if raw.get(f"r{i}_par") is not None)
        processed.append(raw | {"name": p_name, "p_total": p_total})
    team_summaries.append({"owner": owner, "total": calculate_best_4(processed), "players": sorted(processed, key=lambda x: x['p_total'])})

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
        rows += f"<tr><td class='p-name'>{p['name']}</td><td class='{t_style}'>{t_txt}</td><td>{status}</td><td>{format_round_score(p['r1'], p.get('r1_par'))}</td><td>{format_round_score(p['r2'], p.get('r2_par'))}</td><td>{format_round_score(p['r3'], p.get('r3_par'))}</td><td>{format_round_score(p['r4'], p.get('r4_par'))}</td><td class='{tot_style}'>{tot_txt}</td></tr>"

    # WRAPPED IN responsive-table DIV FOR MOBILE SCROLLING
    st.markdown(f"""
    <div class="table-container">
        <div class="table-head">{team["owner"]}'s Roster</div>
        <div class="responsive-table">
            <table class="m-table">
                <thead>
                    <tr><th>Player</th><th>Today</th><th>Status</th><th>R1</th><th>R2</th><th>R3</th><th>R4</th><th>Total</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)
