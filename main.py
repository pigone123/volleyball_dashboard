import streamlit as st

from ui.layout import setup_page
from utils.helpers import horizontal_radio
from utils.constants import EVENT_OUTCOMES, PLAYERS
from services.supabase_service import (
    save_event, load_events, update_event, delete_event
)
from services.export_service import export_all_events_excel
from services.export_service import export_player_excel

setup_page()

st.session_state.video_url = st.text_input("🎥 YouTube Video URL")
if st.session_state.video_url:
    st.video(st.session_state.video_url)

st.session_state.game_name = st.text_input("🏆 Enter Game Name")

player = horizontal_radio("### 🏐 Select Player", PLAYERS, "selected_player")
event = horizontal_radio(
    "### ⚡ Select Event",
    ["", "Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"],
    "selected_event"
)


base_outcomes = EVENT_OUTCOMES.get(event, [])
outcome = horizontal_radio(
    "### 🎯 Select Outcome",
    [""] + base_outcomes,
    "selected_outcome"
) if base_outcomes else None


if st.button("💾 Save Event"):
    if player and event and outcome:
        save_event({
            "player": player,
            "event_category": event,
            "outcome": outcome,
            "game_name": st.session_state.game_name or "No Game Entered",
            "video_url": st.session_state.video_url
        })
        st.success("Saved!")
    else:
        st.error("Missing fields")

st.divider()
st.subheader("📤 Export Data")

df = load_events()
if not df.empty:
    export_all_events_excel(df)


    st.divider()
    st.subheader("📊 Player Statistics Export")

    player_for_export = st.selectbox(
        "Select player",
        sorted(df["player"].dropna().unique())
    )

    if st.button("⬇️ Download Player Excel Report", use_container_width=True):
        export_player_excel(df, player_for_export)
