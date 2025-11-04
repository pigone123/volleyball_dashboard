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

st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

# ------------------ SESSION STATE ------------------
for key in ["selected_player", "selected_event", "selected_outcome"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------ VIDEO INPUT ------------------
video_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

st.markdown("<div style='margin-bottom:0.2rem'></div>", unsafe_allow_html=True)

# ------------------ CLICKABLE BUTTONS ------------------
def clickable_buttons(options, session_key, color):
    cols = st.columns(len(options), gap="small")
    for i, option in enumerate(options):
        selected = st.session_state[session_key] == option
        bg_color = color if selected else "#F0F2F6"
        fg_color = "white" if selected else "black"

        # Wrap in form so each button is independent
        with cols[i]:
            with st.form(key=f"{session_key}_form_{i}", clear_on_submit=False):
                submitted = st.form_submit_button(
                    option,
                    help=f"Select {option}",
                    use_container_width=True
                )
                if submitted:
                    st.session_state[session_key] = option

                # Apply color and style
                st.markdown(
                    f"""
                    <style>
                    div.stButton>button:first-child {{
                        background-color: {bg_color};
                        color: {fg_color};
                        border-radius:6px;
                        padding:0.3em 0.5em;
                        font-size:0.85rem;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

# ------------------ PLAYER ------------------
st.markdown("### 🏐 Select Player")
players = ["Ori","Ofir","Beni","Hillel","Shaked","Omer Saar","Omer","Kart","Lior","Yonatan","Ido","Roi"]
clickable_buttons(players, "selected_player", "#4CAF50")

# ------------------ EVENT ------------------
st.markdown("### ⚡ Select Event")
events = ["Serve","Attack","Block","Receive","Dig","Set","Error"]
clickable_buttons(events, "selected_event", "#2196F3")

# ------------------ OUTCOME ------------------
st.markdown("### 🎯 Select Outcome")
if st.session_state.selected_event == "Serve":
    outcomes = ["Ace","Error","Normal"]
else:
    outcomes = ["Success","Fail","Neutral"]
clickable_buttons(outcomes, "selected_outcome", "#FF9800")

# ------------------ SAVE ------------------
st.markdown("<div style='margin-top:0.2rem; margin-bottom:0.2rem'></div>", unsafe_allow_html=True)
if st.button("💾 Save Event", use_container_width=True):
    p = st.session_state.selected_player
    e = st.session_state.selected_event
    o = st.session_state.selected_outcome
    if p and e and o:
        c.execute(
            "INSERT INTO events (timestamp, player, event, outcome, video_url) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), p, e, o, video_url)
        )
        conn.commit()
        st.success(f"Saved: {p} | {e} | {o}")
        st.session_state.selected_player = None
        st.session_state.selected_event = None
        st.session_state.selected_outcome = None
        st.rerun()
    else:
        st.error("Please select a player, event, and outcome before saving.")

# ------------------ LOGGED EVENTS ------------------
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
