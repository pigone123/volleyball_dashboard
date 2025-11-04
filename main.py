import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ------------------ DATABASE SETUP ------------------
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

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

st.title("🏐 Volleyball Event Dashboard")

# Input: YouTube video
video_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

# Event logging section
st.set_page_config(layout="wide")

# ---------- SESSION STATE ----------
if "selected_player" not in st.session_state:
    st.session_state.selected_player = None
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "selected_outcome" not in st.session_state:
    st.session_state.selected_outcome = None

# ---------- STYLE: tighter spacing ----------
st.markdown("""
<style>
    div[data-testid="stHorizontalBlock"] {
        gap: 0.3rem !important;  /* reduce column gap */
    }
    div.stButton>button {
        margin: 1px 2px !important;  /* reduce vertical & horizontal margin */
        border-radius: 10px;
        padding: 0.3em 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# ---------- PLAYER SELECTION ----------
st.subheader("🏐 בחר שחקן")

players = ["אורי", "אופיר", "בני", "הלל", "שקד", "עומר סער", "עומר", "קארט", "ליאור", "יונתן", "עידו", "רועי"]

cols_players = st.columns(len(players), gap="small")

for i, name in enumerate(players):
    selected = st.session_state.selected_player == name
    if cols_players[i].button(name, key=f"player_{i}"):
        st.session_state.selected_player = name

    st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child({i+1}) button {{
            background-color: {'#4CAF50' if selected else '#F0F2F6'};
            color: {'white' if selected else 'black'};
        }}
        </style>
    """, unsafe_allow_html=True)

player = st.session_state.selected_player
if player:
    st.info(f"🎯 נבחר שחקן: {player}")
else:
    st.warning("אנא בחר שחקן")

# ---------- EVENT SELECTION ----------
st.subheader("⚡ בחר מהלך")

events = ["הגשה", "התקפה", "חסימה", "קבלה", "חפירה", "מסירה", "שגיאה"]

cols_events = st.columns(len(events), gap="small")

for i, e in enumerate(events):
    selected = st.session_state.selected_event == e
    if cols_events[i].button(e, key=f"event_{i}"):
        st.session_state.selected_event = e

    st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child({i+1}) button {{
            background-color: {'#2196F3' if selected else '#F0F2F6'};
            color: {'white' if selected else 'black'};
        }}
        </style>
    """, unsafe_allow_html=True)

event_type = st.session_state.selected_event
if event_type:
    st.info(f"⚙️ נבחר מהלך: {event_type}")
else:
    st.warning("אנא בחר מהלך")

# ---------- OUTCOME SELECTION ----------
st.subheader("🎯 בחר תוצאה")

if event_type == "הגשה":
    outcomes = ["אייס", "שגיאה", "ביצוע רגיל"]
else:
    outcomes = ["הצלחה", "כישלון", "ניטרלי"]

cols_outcomes = st.columns(len(outcomes), gap="small")

for i, outcome_name in enumerate(outcomes):
    selected = st.session_state.selected_outcome == outcome_name
    if cols_outcomes[i].button(outcome_name, key=f"outcome_{i}"):
        st.session_state.selected_outcome = outcome_name

    st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child({i+1}) button {{
            background-color: {'#FF9800' if selected else '#F0F2F6'};
            color: {'white' if selected else 'black'};
        }}
        </style>
    """, unsafe_allow_html=True)

outcome = st.session_state.selected_outcome
if outcome:
    st.info(f"✅ נבחרה תוצאה: {outcome}")
else:
    st.warning("אנא בחר תוצאה")

# ---------- SAVE BUTTON ----------
st.markdown("---")
if st.button("💾 שמור מהלך"):
    if player and event_type and outcome:
        st.success(f"נשמר: {player} | {event_type} | {outcome}")

        # Here you can insert into your database
        # save_to_db(player, event_type, outcome)

        # Reset selections for next event
        st.session_state.selected_player = None
        st.session_state.selected_event = None
        st.session_state.selected_outcome = None
        st.rerun()
    else:
        st.error("אנא בחר שחקן, מהלך ותוצאה לפני שמירה")


player = st.session_state.selected_player
event_type = st.session_state.selected_event
outcome = st.session_state.selected_outcome

if st.button("Save Event"):
    if not player:
        st.warning("Please enter the player's name.")
    else:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_url) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), player, event_type, outcome, video_url)
        )
        conn.commit()
        st.success(f"Event saved for {player} ✅")

# ------------------ DISPLAY SAVED DATA ------------------
st.subheader("📊 Logged Events")

df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)

if len(df) > 0:
    # Filter bar
    with st.expander("🔍 Filters"):
        selected_player = st.multiselect("Filter by Player", df["player"].unique())
        selected_event = st.multiselect("Filter by Event Type", df["event"].unique())

        if selected_player:
            df = df[df["player"].isin(selected_player)]
        if selected_event:
            df = df[df["event"].isin(selected_event)]

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "⬇️ Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="volleyball_events.csv",
        mime="text/csv"
    )
else:
    st.info("No events logged yet.")
