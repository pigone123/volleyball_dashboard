import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import time

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return psycopg2.connect(
        user=st.secrets["postgres"]["USER"],
        password=st.secrets["postgres"]["PASSWORD"],
        host=st.secrets["postgres"]["HOST"],
        port=st.secrets["postgres"]["PORT"],
        dbname=st.secrets["postgres"]["DBNAME"]
    )

def safe_execute(cursor, conn, query, params=()):
    """Run a query safely with retry if the database is busy."""
    for attempt in range(5):
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except psycopg2.OperationalError as e:
            if "could not obtain lock" in str(e):
                time.sleep(0.2)
            else:
                raise
    st.error("⚠️ Database is busy, please try again in a moment.")
    return False

# ---------------- CREATE TABLE IF NOT EXISTS ----------------
with get_connection() as conn:
    with conn.cursor() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            player TEXT,
            event TEXT,
            outcome TEXT,
            video_time TEXT,
            video_url TEXT,
            game_name TEXT
        );
        """)
        conn.commit()

# ---------------- STREAMLIT PAGE CONFIG ----------------
st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

# ---------------- SESSION STATE ----------------
for key in ["selected_player", "selected_event", "selected_outcome", "attack_type", "set_to", "game_name"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- VIDEO INPUT ----------------
video_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

st.markdown("<div style='margin-bottom:0.5rem'></div>", unsafe_allow_html=True)

# ---------------- GAME INFO ----------------
game_name = st.text_input("🏆 Enter Game Name", placeholder="e.g. Blich vs Ramat Gan")
if game_name:
    st.session_state["game_name"] = game_name
elif "game_name" in st.session_state:
    game_name = st.session_state["game_name"]

# ---------------- HELPER FUNCTION ----------------
def horizontal_radio(label, options, session_key):
    selected = st.session_state.get(session_key)
    value = st.radio(
        label,
        options,
        index=options.index(selected) if selected in options else 0,
        horizontal=True
    )
    st.session_state[session_key] = value
    return value

# ---------------- PLAYER SELECTION ----------------
st.markdown("### 🏐 Select Player")
player = horizontal_radio("", ["Ori","Ofir","Beni","Hillel","Shak","Omer Saar","Omer","Karat","Lior","Yonatan","Ido","Royi"], "selected_player")

# ---------------- EVENT SELECTION ----------------
st.markdown("### ⚡ Select Event")
event = horizontal_radio("", ["Serve","Attack","Block","Receive","Dig","Set"], "selected_event")

# ---------------- EVENT-SPECIFIC SUBCHOICES ----------------
attack_type = None
set_to = None

event_outcomes = {
    "Serve": ["Ace", "Out", "Net", "In", "Off System"],
    "Attack": ["Blockout", "Out", "Net", "In Play", "Off System"],
    "Block": ["Blockout", "Touch", "Kill", "Softblock", "Error"],
    "Receive": ["Good", "Neutral", "Bad"],
    "Dig": ["Good", "Neutral", "Bad"],
    "Set": ["0 Blockers", "1 Blocker", "2 Blocker"]
}

if event == "Attack":
    st.markdown("### ⚡ Attack Type")
    attack_type = horizontal_radio("", ["Free Ball", "Tip", "Hole", "Spike"], "attack_type")

elif event == "Set":
    st.markdown("### 🧱 Set To")
    set_to = horizontal_radio("", ["Position 1", "Position 2", "Position 3", "Position 4", "Position 6"], "set_to")

# ---------------- OUTCOME SELECTION ----------------
base_outcomes = event_outcomes.get(event, [])
if event == "Attack" and st.session_state.get("attack_type") == "Spike":
    outcome_options = base_outcomes + ["Hard Blocked", "Soft Blocked", "Kill"]
else:
    outcome_options = base_outcomes

st.markdown("### 🎯 Select Outcome")
if outcome_options:
    outcome = horizontal_radio("", outcome_options, "selected_outcome")
else:
    outcome = None

# ---------------- SAVE EVENT ----------------
st.markdown("<div style='margin-top:0.5rem; margin-bottom:0.5rem'></div>", unsafe_allow_html=True)
if st.button("💾 Save Event", use_container_width=True):
    p = st.session_state.get("selected_player")
    e = st.session_state.get("selected_event")
    o = st.session_state.get("selected_outcome")
    a_type = st.session_state.get("attack_type") if e == "Attack" else None
    s_to = st.session_state.get("set_to") if e == "Set" else None

    if p and e and o:
        extra_info = a_type or s_to
        with get_connection() as conn:
            with conn.cursor() as c:
                safe_execute(
                    c, conn,
                    "INSERT INTO events (timestamp, player, event, outcome, video_url, game_name) VALUES (%s, %s, %s, %s, %s, %s)",
                    (datetime.now(), p, f"{e} ({extra_info})" if extra_info else e, o, video_url, game_name)
                )
        st.success(f"Saved: {p} | {e} | {extra_info if extra_info else ''} | {o}")

        # Reset session state
        for key in ["selected_player", "selected_event", "selected_outcome", "attack_type", "set_to"]:
            st.session_state[key] = None
        st.rerun()
    else:
        st.error("Please select a player, event, and outcome before saving.")

# ---------------- LOGGED EVENTS ----------------
st.markdown("<hr style='margin-top:0.2rem;margin-bottom:0.2rem'>", unsafe_allow_html=True)
st.markdown("### 📊 Logged Events")
with get_connection() as conn:
    df = pd.read_sql("SELECT * FROM events ORDER BY id DESC", conn)

if not df.empty:
    with st.expander("🔍 Filter"):
        sel_game = st.multiselect("Game", df["game_name"].dropna().unique())
        sel_player = st.multiselect("Player", df["player"].unique())
        sel_event = st.multiselect("Event", df["event"].unique())
    
        if sel_game:
            df = df[df["game_name"].isin(sel_game)]
        if sel_player:
            df = df[df["player"].isin(sel_player)]
        if sel_event:
            df = df[df["event"].isin(sel_event)]
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), "volleyball_events.csv", "text/csv")
else:
    st.info("No events logged yet.")

# ---------------- DANGER ZONE ----------------
st.markdown("---")
st.markdown("### ⚠️ Danger Zone")
if st.button("🗑️ Clear All Events", use_container_width=True):
    with get_connection() as conn:
        with conn.cursor() as c:
            safe_execute(c, conn, "DELETE FROM events")
    for key in ["selected_player", "selected_event", "selected_outcome", "attack_type", "set_to"]:
        st.session_state[key] = None
    st.success("✅ All events have been cleared!")
