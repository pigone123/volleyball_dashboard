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

# ---------- STYLE: compact layout ----------
st.markdown("""
<style>
    section[data-testid="stSidebar"] {width: 250px !important;}
    div.block-container {padding-top: 1rem; padding-bottom: 0.5rem; padding-left: 2rem; padding-right: 2rem;}
    h1, h2, h3 {margin-bottom: 0.3rem;}
    div[data-testid="stHorizontalBlock"] {gap: 0.25rem !important;}
    div.stButton > button {
        margin: 1px 2px !important;
        border-radius: 8px;
        padding: 0.3em 0.6em;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.title("🏐 Volleyball Event Dashboard")

# ------------------ VIDEO INPUT ------------------
video_url = st.text_input("🎥 כתובת וידאו מיוטיוב", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

st.markdown("---")

# ---------- SESSION STATE ----------
if "selected_player" not in st.session_state:
    st.session_state.selected_player = None
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "selected_outcome" not in st.session_state:
    st.session_state.selected_outcome = None

# ---------- HELPER FUNCTION ----------
def button_group(options, key_prefix, color, selected_value):
    """Display a compact horizontal row of selectable buttons"""
    cols = st.columns(len(options), gap="small")
    new_selection = selected_value
    for i, name in enumerate(options):
        is_selected = (name == selected_value)
        style = f"background-color:{color};color:white;" if is_selected else "background-color:#F0F2F6;color:black;"
        with cols[i]:
            if st.button(name, key=f"{key_prefix}_{i}", use_container_width=True):
                new_selection = name
        st.markdown(
            f"<style>div[data-testid='column']:has(> div button#{key_prefix}_{i}) button{{{style}}}</style>",
            unsafe_allow_html=True
        )
    return new_selection

# ---------- PLAYER SELECTION ----------
st.markdown("#### 🏐 בחר שחקן")
players = ["אורי", "אופיר", "בני", "הלל", "שקד", "עומר סער", "עומר", "קארט", "ליאור", "יונתן", "עידו", "רועי"]
st.session_state.selected_player = button_group(players, "player", "#4CAF50", st.session_state.selected_player)

# ---------- EVENT SELECTION ----------
st.markdown("#### ⚡ בחר מהלך")
events = ["הגשה", "התקפה", "חסימה", "קבלה", "חפירה", "מסירה", "שגיאה"]
st.session_state.selected_event = button_group(events, "event", "#2196F3", st.session_state.selected_event)

# ---------- OUTCOME SELECTION ----------
st.markdown("#### 🎯 בחר תוצאה")
if st.session_state.selected_event == "הגשה":
    outcomes = ["אייס", "שגיאה", "ביצוע רגיל"]
else:
    outcomes = ["הצלחה", "כישלון", "ניטרלי"]
st.session_state.selected_outcome = button_group(outcomes, "outcome", "#FF9800", st.session_state.selected_outcome)

# ---------- SAVE BUTTON ----------
st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
if st.button("💾 שמור מהלך", use_container_width=True):
    p, e, o = st.session_state.selected_player, st.session_state.selected_event, st.session_state.selected_outcome
    if p and e and o:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_url) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), p, e, o, video_url)
        )
        conn.commit()
        st.success(f"נשמר: {p} | {e} | {o}")
        # reset for next entry
        st.session_state.selected_player = None
        st.session_state.selected_event = None
        st.session_state.selected_outcome = None
        st.rerun()
    else:
        st.error("אנא בחר שחקן, מהלך ותוצאה לפני שמירה")

st.markdown("---")

# ---------- DISPLAY SAVED DATA ----------
st.markdown("#### 📊 מהלכים שנשמרו")
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
    st.download_button(
        "⬇️ הורד כ-CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="volleyball_events.csv",
        mime="text/csv"
    )
else:
    st.info("אין מהלכים שמורים עדיין.")
