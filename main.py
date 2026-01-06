import streamlit as st

from ui.layout import setup_page
from utils.helpers import horizontal_radio
from utils.constants import EVENT_OUTCOMES, PLAYERS
from services.supabase_service import (
    save_event, load_events, update_event, delete_event
)
from services.export_service import (
    export_all_events_excel,
    export_player_excel
)

# ---------------- PAGE SETUP ----------------
setup_page()

# ---------------- VIDEO INPUT ----------------
st.session_state.video_url = st.text_input("🎥 YouTube Video URL")
if st.session_state.video_url:
    st.video(st.session_state.video_url)

# ---------------- GAME INFO ----------------
st.session_state.game_name = st.text_input("🏆 Enter Game Name")

# ---------------- MAIN SELECTION ----------------
player = horizontal_radio("### 🏐 Select Player", PLAYERS, "selected_player")

event = horizontal_radio(
    "### ⚡ Select Event",
    ["", "Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"],
    "selected_event"
)

# ---------------- SUBCHOICES ----------------
attack_type = None
set_to = None

if event == "Attack":
    attack_type = horizontal_radio(
        "### ⚡ Attack Type",
        ["", "Free Ball", "Tip", "Hole", "Spike"],
        "attack_type"
    )

elif event == "Set":
    set_to = horizontal_radio(
        "### 🧱 Set To",
        ["", "Position 1", "Position 2", "Position 3", "Position 4", "Position 6"],
        "set_to"
    )

# ---------------- OUTCOME ----------------
base_outcomes = EVENT_OUTCOMES.get(event, [])

# Reset outcome if attack type changes
if event == "Attack":
    if st.session_state.get("last_attack_type") != attack_type:
        st.session_state.selected_outcome = ""
    st.session_state.last_attack_type = attack_type

# Add spike-specific outcomes
if event == "Attack" and attack_type == "Spike":
    outcome_options = base_outcomes + ["Hard Blocked", "Soft Blocked"]
else:
    outcome_options = base_outcomes

outcome = (
    horizontal_radio(
        "### 🎯 Select Outcome",
        [""] + outcome_options,
        "selected_outcome"
    )
    if outcome_options else None
)

# ---------------- SAVE EVENT ----------------
if st.button("💾 Save Event", use_container_width=True):
    if player and event and outcome:
        save_event({
            "player": player,
            "event_category": event,
            "attack_type": attack_type if event == "Attack" else None,
            "set_to": set_to if event == "Set" else None,
            "outcome": outcome,
            "game_name": st.session_state.game_name or "No Game Entered",
            "video_url": st.session_state.video_url
        })
        st.success("✅ Event saved!")
    else:
        st.error("⚠️ Please select player, event and outcome")

# ---------------- LOGGED EVENTS ----------------
st.divider()
st.subheader("📋 Logged Events")

df = load_events()

if not df.empty:
    sort_col = "timestamp" if "timestamp" in df.columns else "id"
    df = df.sort_values(sort_col, ascending=False)

    df_display = df.copy()
    df_display["Delete?"] = False

    edited_df = st.data_editor(
        df_display,
        disabled=["id"],
        num_rows="fixed",
        use_container_width=True,
        key="events_editor"
    )

    # ----- Save edits -----
    if st.button("💾 Save All Changes", use_container_width=True):
        for _, row in edited_df.iterrows():
            original = df.loc[df["id"] == row["id"]].iloc[0]
            changes = {
                col: row[col]
                for col in df.columns
                if col in row and row[col] != original[col]
            }
            if changes:
                update_event(row["id"], changes)

        st.success("✅ All changes saved!")
        st.rerun()

    # ----- Delete rows -----
    delete_ids = edited_df.loc[edited_df["Delete?"], "id"].tolist()

    if delete_ids:
        if st.button("🗑️ Delete Selected Rows", use_container_width=True):
            for row_id in delete_ids:
                delete_event(row_id)
            st.success("🗑️ Rows deleted")
            st.rerun()

    # ---------------- EXPORTS ----------------
    st.divider()
    st.subheader("📤 Export Data")
    export_all_events_excel(df)

    st.divider()
    st.subheader("📊 Player Statistics Export")

    player_for_export = st.selectbox(
        "Select player",
        sorted(df["player"].dropna().unique())
    )

    if st.button("⬇️ Download Player Excel Report", use_container_width=True):
        export_player_excel(df, player_for_export)

else:
    st.info("No events logged yet.")
