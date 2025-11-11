import streamlit as st
import pandas as pd
import requests
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

# Initialize all session_state variables
for key in [
    "video_url", "game_name", "set_number",
    "selected_player", "selected_event",
    "selected_outcome", "attack_type", "set_to"
]:
    st.session_state.setdefault(key, "")

# ---------------- VIDEO INPUT ----------------
st.session_state.video_url = st.text_input(
    "🎥 YouTube Video URL",
    value=st.session_state.video_url,
    placeholder="https://www.youtube.com/watch?v=example",
    key="video_url_input"
)
if st.session_state.video_url:
    st.video(st.session_state.video_url)

# ---------------- GAME INFO ----------------
st.session_state.game_name = st.text_input(
    "🏆 Enter Game Name",
    value=st.session_state.game_name,
    placeholder="e.g. Blich vs Ramat Gan",
    key="game_name_input"
)

st.session_state.set_number = st.selectbox(
    "🎯 Select Set Number (optional)",
    ["", "1st Set", "2nd Set", "3rd Set", "4th Set", "5th Set"],
    index=["", "1st Set", "2nd Set", "3rd Set", "4th Set", "5th Set"].index(st.session_state.set_number)
    if st.session_state.set_number in ["", "1st Set", "2nd Set", "3rd Set", "4th Set", "5th Set"] else 0,
    key="set_number_select"
)

# ---------------- HELPER ----------------
def horizontal_buttons(label, options, session_key):
    """Creates a horizontal button group that behaves like radio buttons."""
    st.markdown(f"#### {label}")
    cols = st.columns(len(options))
    selected = st.session_state.get(session_key, options[0])

    # Add custom CSS for highlighting
    st.markdown("""
        <style>
        div[data-testid="column"] button[kind="secondary"] {
            border-radius: 10px;
            padding: 0.5rem 1rem;
            margin: 0.2rem;
            border: 1px solid #ccc;
            transition: all 0.2s ease-in-out;
        }
        div[data-testid="column"] button[kind="secondary"]:hover {
            background-color: #f0f2f6;
            border-color: #aaa;
        }
        div[data-testid="column"] button[selected="true"] {
            background-color: #00b4d8 !important;
            color: white !important;
            border-color: #0096c7 !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    for i, opt in enumerate(options):
        is_selected = (opt == selected)
        button_label = opt if opt else "—"
        button_placeholder = cols[i].empty()
        if button_placeholder.button(button_label, key=f"{session_key}_{i}", use_container_width=True):
            st.session_state[session_key] = opt
            st.rerun()
        # Inject custom attribute for highlighting (works by DOM attribute)
        st.markdown(
            f"<script>var btn = window.parent.document.querySelectorAll('button[kind=\"secondary\"]')[{i}]; if (btn && '{str(is_selected).lower()}'=='true') btn.setAttribute('selected', 'true');</script>",
            unsafe_allow_html=True,
        )

    return st.session_state.get(session_key, options[0])


# ---------------- PLAYER SELECTION ----------------
player = horizontal_buttons("### 🏐 Select Player", 
    ["", "Ori", "Ofir", "Beni", "Hillel", "Shak", "Omer Saar", "Omer", "Karat", "Lior", "Yonatan", "Ido", "Royi"], 
    "selected_player"
)

# ---------------- EVENT SELECTION ----------------
event = horizontal_buttons("### ⚡ Select Event", 
    ["", "Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"], 
    "selected_event"
)

# ---------------- SUBCHOICES ----------------
attack_type = None
set_to = None

event_outcomes = {
    "Serve": ["Ace", "Out", "Net", "In", "Off System"],
    "Attack": ["Blockout", "Out", "Net", "In Play", "Off System"],
    "Block": ["Blockout", "Touch", "Kill", "Softblock", "Error"],
    "Receive": ["Good", "Neutral", "Bad"],
    "Dig": ["Good", "Neutral", "Bad"],
    "Set": ["0 Blockers", "1 Blocker", "2 Blocker"],
    "Defense": ["Good", "Neutral", "Bad"]
}

if event == "Attack":
    attack_type = horizontal_radio("### ⚡ Attack Type", ["", "Free Ball", "Tip", "Hole", "Spike"], "attack_type")
elif event == "Set":
    set_to = horizontal_radio("### 🧱 Set To", ["", "Position 1", "Position 2", "Position 3", "Position 4", "Position 6"], "set_to")

# ---------------- OUTCOME ----------------
base_outcomes = event_outcomes.get(event, [])
if event == "Attack" and st.session_state.get("attack_type") == "Spike":
    outcome_options = base_outcomes + ["Hard Blocked", "Soft Blocked", "Kill"]
else:
    outcome_options = base_outcomes

outcome = (
    horizontal_radio("### 🎯 Select Outcome", [""] + outcome_options, "selected_outcome")
    if outcome_options else None
)

# ---------------- SUPABASE OPS ----------------
def save_event():
    extra_info = attack_type if attack_type else set_to
    data = {
        "player": player,
        "event": f"{event} ({extra_info})" if extra_info else event,
        "outcome": outcome,
        "video_url": st.session_state.video_url,
        "game_name": st.session_state.game_name,
        "set_number": st.session_state.set_number if st.session_state.set_number else None
    }

    response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=HEADERS, data=json.dumps(data))
    if response.status_code in [200, 201]:
        st.success(f"✅ Saved: {player} | {event} | {extra_info if extra_info else ''} | {outcome}")
    else:
        st.error(f"❌ Failed to save: {response.text}")

def load_events():
    response = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=HEADERS)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"Failed to load events: {response.text}")
        return pd.DataFrame()

def update_event(row_id, updated_data):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(updated_data))
    if response.status_code not in [200, 204]:
        st.error(f"❌ Failed to update row {row_id}: {response.text}")

def delete_event(row_id):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code not in [200, 204]:
        st.error(f"❌ Failed to delete row {row_id}: {response.text}")

# ---------------- SAVE BUTTON ----------------
if st.button("💾 Save Event", use_container_width=True):
    if player and event and outcome:
        save_event()
    else:
        st.error("⚠️ Please select a player, event, and outcome before saving.")

# ---------------- LOGGED EVENTS ----------------
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

    # -------- Editable + Deletable Table --------
    df_display = df.drop(columns=["timestamp"], errors="ignore").copy()
    df_display["Delete?"] = False  # Add a checkbox column

    edited_df = st.data_editor(
        df_display,
        num_rows="fixed",
        use_container_width=True,
        key="editor",
    )

    # Handle edits
    if st.button("💾 Save All Changes", use_container_width=True):
        for i, row in edited_df.iterrows():
            original = df.loc[df["id"] == row["id"]].iloc[0]
            changes = {col: row[col] for col in df.columns if col in row and row[col] != original[col]}
            if changes:
                update_event(row["id"], changes)
        st.success("✅ All edits saved!")
        st.rerun()

    # Handle deletes
    delete_ids = edited_df.loc[edited_df["Delete?"], "id"].tolist()
    if delete_ids and st.button("🗑️ Delete Selected Rows", use_container_width=True):
        for row_id in delete_ids:
            delete_event(row_id)
        st.rerun()

    # CSV Export
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), "volleyball_events.csv", "text/csv")

else:
    st.info("No events logged yet.")
