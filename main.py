import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ---------------- DATABASE ----------------
conn = sqlite3.connect("volleyball_events.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    player TEXT,
    event TEXT,
    outcome TEXT,
    video_time TEXT,
    video_url TEXT
)
""")
conn.commit()

st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

# ---------------- SESSION STATE ----------------
for key in ["selected_player", "selected_event", "selected_outcome"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- VIDEO INPUT ----------------
video_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

st.markdown("<div style='margin-bottom:0.5rem'></div>", unsafe_allow_html=True)

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
player = horizontal_radio("", ["Ori","Ofir","Beni","Hillel","Shaked","Omer Saar","Omer","Kart","Lior","Yonatan","Ido","Roi"], "selected_player")

# ---------------- EVENT SELECTION ----------------
st.markdown("### ⚡ Select Event")
event = horizontal_radio("", ["Serve","Attack","Block","Receive","Dig","Set"], "selected_event")

# ---------------- OUTCOME SELECTION ----------------
attack_type = None
st.markdown("### 🎯 Select Outcome")

event_outcomes = {
    "Serve": ["Ace","Out","Net","Good","Neutral","Bad"],
    "Attack": ["Blockout","Out","Net","Good","Neutral","Bad"],
    "Block": ["Blockout","Touch","Net","Good","Neutral", "Bad"],
    "Receive": ["Good","Netural","Bad"],
    "Dig": ["Good","Netural","Bad"],
    "Set": ["Reach Antenna","Didn't Reach Antenna","Overpass Antenna"]
}


if event == "Attack":
    st.markdown("### ⚡ Attack Type")
    attack_type = horizontal_radio("", ["Free Ball", "Tip", "Hole", "Spike"], "attack_type")


outcome_options = event_outcomes.get(event, [])

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

    if p and e and o:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_url) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), p, f"{e} ({a_type})" if a_type else e, o, video_url)
        )
        conn.commit()
        st.success(f"Saved: {p} | {e} | {a_type if a_type else ''} | {o}")
        
        # Reset selections
        st.session_state["selected_player"] = None
        st.session_state["selected_event"] = None
        st.session_state["selected_outcome"] = None
        st.session_state["attack_type"] = None
        st.rerun()
    else:
        st.error("Please select a player, event, and outcome before saving.")
# ---------------- LOGGED EVENTS ----------------
st.markdown("<hr style='margin-top:0.2rem;margin-bottom:0.2rem'>", unsafe_allow_html=True)
st.markdown("### 📊 Logged Events")
df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
if not df.empty:
    with st.expander("🔍 Filter"):
        sel_player = st.multiselect("Player", df["player"].unique())
        sel_event = st.multiselect("Event", df["event"].unique())
        if sel_player:
            df = df[df["player"].isin(sel_player)]
        if sel_event:
            df = df[df["event"].isin(sel_event)]
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), "volleyball_events.csv", "text/csv")
else:
    st.info("No events logged yet.")


st.markdown("---")
st.markdown("### ⚠️ Danger Zone")

# Show confirmation checkbox first
confirm_clear = st.checkbox("Are you sure you want to delete all events?", key="confirm_clear")

if confirm_clear:
    if st.button("🗑️ Clear All Events", use_container_width=True):
        # Clear database
        with sqlite3.connect("volleyball_events.db") as conn_clear:
            c_clear = conn_clear.cursor()
            c_clear.execute("DELETE FROM events")
            conn_clear.commit()

        # Reset session state
        for key in ["selected_player", "selected_event", "selected_outcome", "attack_type"]:
            if key in st.session_state:
                st.session_state[key] = None

        st.success("✅ All events have been cleared!")

        # Rerun after database cleared and session reset
        st.experimental_rerun()
