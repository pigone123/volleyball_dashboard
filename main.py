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
st.subheader("📋 Log New Event")
st.subheader("בחר שחקן")
players = ["אורי", "אופיר", "בני", "הלל", "שקד", "עומר סער", "עומר", "קארט", "ליאור", "יונתן", "עידו", "רועי"]

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

cols = st.columns(4)  # how many buttons per row
for i, name in enumerate(players):
    if cols[i % 4].button(name):
        st.session_state.selected_player = name

player = st.session_state.get("selected_player")
if player:
    st.info(f"🎯 נבחר שחקן: {player}")
else:
    st.warning("אנא בחר שחקן")

# --- Now only 2 columns for event + outcome ---
col2, col3 = st.columns(2)

with col2:
    event_type = st.selectbox("מהלך", ["הגשה", "התקפה", "חסימה", "קבלה", "חפירה", "מסירה"])

with col3:
    # You can dynamically change the outcome options depending on the event
    if event_type == "הגשה":
        outcome = st.selectbox("תוצאה", ["שגיאה", "אייס", "ביצוע רגיל"])
    else:
        outcome = st.selectbox("תוצאה", ["הצלחה", "כישלון", "ניטרלי"])

video_time = st.text_input("Video Time (optional, e.g. 12:34)")

if st.button("Save Event"):
    if not player:
        st.warning("Please enter the player's name.")
    else:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_time, video_url) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), player, event_type, outcome, video_time, video_url)
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
