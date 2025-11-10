import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import os
import json

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"] 
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"] 
TABLE_NAME = "Volleyball_events"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(page_title="🏐 Volleyball Event Dashboard", layout="wide")

for key in ["selected_player", "selected_event", "selected_outcome", "attack_type", "set_to", "game_name"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- VIDEO INPUT ----------------
video_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
if video_url:
    st.video(video_url)

# ---------------- GAME INFO ----------------
game_name = st.text_input("🏆 Enter Game Name", placeholder="e.g. Blich vs Ramat Gan")
if game_name:
    st.session_state["game_name"] = game_name
elif "game_name" in st.session_state:
    game_name = st.session_state["game_name"]

# ---------------- HELPER ----------------
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
player = horizontal_radio("### 🏐 Select Player", ["Ori","Ofir","Beni","Hillel","Shak","Omer Saar","Omer","Karat","Lior","Yonatan","Ido","Royi"], "selected_player")

# ---------------- EVENT SELECTION ----------------
event = horizontal_radio("### ⚡ Select Event", ["Serve","Attack","Block","Receive","Dig","Set"], "selected_event")

# ---------------- SUBCHOICES ----------------
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
    attack_type = horizontal_radio("### ⚡ Attack Type", ["Free Ball", "Tip", "Hole", "Spike"], "attack_type")
elif event == "Set":
    set_to = horizontal_radio("### 🧱 Set To", ["Position 1", "Position 2", "Position 3", "Position 4", "Position 6"], "set_to")

# ---------------- OUTCOME ----------------
base_outcomes = event_outcomes.get(event, [])
if event == "Attack" and st.session_state.get("attack_type") == "Spike":
    outcome_options = base_outcomes + ["Hard Blocked", "Soft Blocked", "Kill"]
else:
    outcome_options = base_outcomes

outcome = horizontal_radio("### 🎯 Select Outcome", outcome_options, "selected_outcome") if outcome_options else None

# ---------------- SAVE EVENT ----------------
def save_event():
    extra_info = attack_type if attack_type else set_to
    data = {
        "timestamp": datetime.now().isoformat(),
        "player": player,
        "event": f"{event} ({extra_info})" if extra_info else event,
        "outcome": outcome,
        "video_url": video_url,
        "game_name": game_name
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=HEADERS, data=json.dumps(data))
    if response.status_code in [200, 201]:
        st.success(f"Saved: {player} | {event} | {extra_info if extra_info else ''} | {outcome}")
        for key in ["selected_player","selected_event","selected_outcome","attack_type","set_to"]:
            st.session_state[key] = None
    else:
        st.error(f"Failed to save: {response.text}")

if st.button("💾 Save Event", use_container_width=True):
    if player and event and outcome:
        save_event()
    else:
        st.error("Please select a player, event, and outcome before saving.")

# ---------------- LOGGED EVENTS ----------------
def load_events():
    query = f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC"
    response = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=HEADERS)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"Failed to load events: {response.text}")
        return pd.DataFrame()

df = load_events()
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
