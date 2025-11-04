import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ------------------ DATABASE ------------------
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

# ------------------ STREAMLIT CONFIG ------------------
st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

# ------------------ SESSION STATE ------------------
for key in ["selected_player", "selected_event", "selected_outcome"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------ VIDEO INPUT ------------------
video_url = st.text_input("🎥 כתובת וידאו מיוטיוב", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

# Small spacing
st.markdown("<div style='margin-bottom:0.2rem'></div>", unsafe_allow_html=True)

# ------------------ HELPER FUNCTION ------------------
def button_row(options, session_key, color):
    """Display a row of buttons; update session state; highlight selected"""
    cols = st.columns(len(options), gap="small")
    for i, option in enumerate(options):
        # Check if this option is currently selected
        selected = st.session_state[session_key] == option
        # Button color
        bg = color if selected else "#F0F2F6"
        fg = "white" if selected else "black"
        if cols[i].button(option, key=f"{session_key}_{i}", use_container_width=True):
            st.session_state[session_key] = option
        # Apply inline style directly on the button
        cols[i].markdown(
            f"<style>div.stButton>button:nth-child(1){{background-color:{bg};color:{fg};border-radius:6px;padding:0.3em 0.5em;font-size:0.85rem;}}</style>",
            unsafe_allow_html=True
        )

# ------------------ PLAYER SELECTION ------------------
st.markdown("### 🏐 בחר שחקן")
players = ["אורי","אופיר","בני","הלל","שקד","עומר סער","עומר","קארט","ליאור","יונתן","עידו","רועי"]
button_row(players, "selected_player", "#4CAF50")

# ------------------ EVENT SELECTION ------------------
st.markdown("### ⚡ בחר מהלך")
events = ["הגשה","התקפה","חסימה","קבלה","חפירה","מסירה","שגיאה"]
button_row(events, "selected_event", "#2196F3")

# ------------------ OUTCOME SELECTION ------------------
st.markdown("### 🎯 בחר תוצאה")
if st.session_state.selected_event == "הגשה":
    outcomes = ["אייס","שגיאה","ביצוע רגיל"]
else:
    outcomes = ["הצלחה","כישלון","ניטרלי"]
button_row(outcomes, "selected_outcome", "#FF9800")

# ------------------ SAVE BUTTON ------------------
st.markdown("<div style='margin-top:0.2rem; margin-bottom:0.2rem'></div>", unsafe_allow_html=True)
if st.button("💾 שמור מהלך", use_container_width=True):
    p = st.session_state.selected_player
    e = st.session_state.selected_event
    o = st.session_state.selected_outcome
    if p and e and o:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_url) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), p, e, o, video_url)
        )
        conn.commit()
        st.success(f"נשמר: {p} | {e} | {o}")
        # Reset for next event
        st.session_state.selected_player = None
        st.session_state.selected_event = None
        st.session_state.selected_outcome = None
        st.rerun()
    else:
        st.error("אנא בחר שחקן, מהלך ותוצאה לפני שמירה")

# ------------------ DISPLAY SAVED EVENTS ------------------
st.markdown("<hr style='margin-top:0.2rem;margin-bottom:0.2rem'>", unsafe_allow_html=True)
st.markdown("### 📊 מהלכים שנשמרו")
df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
if not df.empty:
    with st.expander("🔍 סינון"):
        sel_player = st.multiselect("שחקן", df["player"].unique())
        sel_event = st.multiselect("מהלך", df["event"].unique())
        if sel_player:
            df = df[df["player"].isin(sel_player)]
        if sel_event:
            df = df[df["event"].isin(sel_event)]
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ הורד כ-CSV", df.to_csv(index=False).encode("utf-8"), "volleyball_events.csv", "text/csv")
else:
    st.info("אין מהלכים שמורים עדיין.")
