import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="🏐 Volleyball Event Dashboard",
        layout="wide"
    )

    for key in [
        "video_url", "game_name", "set_number",
        "selected_player", "selected_event",
        "selected_outcome", "attack_type", "set_to"
    ]:
        st.session_state.setdefault(key, "")
