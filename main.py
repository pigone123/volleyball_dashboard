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
st.subheader("📋 Logged Events")

df = load_events()

if not df.empty:
    # Sort newest first if possible
    sort_col = "timestamp" if "timestamp" in df.columns else "id"
    df = df.sort_values(sort_col, ascending=False)

    # ---------- Editable table ----------
    df_display = df.copy()
    df_display["Delete?"] = False

    edited_df = st.data_editor(
        df_display,
        num_rows="fixed",
        disabled=["id"],
        use_container_width=True,
        key="events_editor"
    )

    # ---------- Save edits ----------
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

    # ---------- Delete selected rows ----------
    delete_ids = edited_df.loc[edited_df["Delete?"], "id"].tolist()

    if delete_ids:
        if st.button("🗑️ Delete Selected Rows", use_container_width=True):
            for row_id in delete_ids:
                delete_event(row_id)

            st.success("🗑️ Selected rows deleted.")
            st.rerun()

    # ---------- Export section ----------
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
