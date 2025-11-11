import os
import json
import requests
import pandas as pd
from dash import Dash, dcc, html, dash_table, ctx
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "Volleyball_events"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------------- DASH APP ----------------
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# ---------------- CONSTANTS ----------------
PLAYERS = ["Ori", "Ofir", "Beni", "Hillel", "Shak", "Omer Saar", "Omer", "Karat", "Lior", "Yonatan", "Ido", "Royi"]
EVENTS = ["Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"]
ATTACK_TYPES = ["Free Ball", "Tip", "Hole", "Spike"]
SET_TO = ["Position 1", "Position 2", "Position 3", "Position 4", "Position 6"]

EVENT_OUTCOMES = {
    "Serve": ["Ace", "Out", "Net", "In", "Off System"],
    "Attack": ["Blockout", "Out", "Net", "In Play", "Off System"],
    "Block": ["Blockout", "Touch", "Kill", "Softblock", "Error"],
    "Receive": ["Good", "Neutral", "Bad"],
    "Dig": ["Good", "Neutral", "Bad"],
    "Set": ["0 Blockers", "1 Blocker", "2 Blocker"],
    "Defense": ["Good", "Neutral", "Bad"]
}

# ---------------- HELPER FUNCTIONS ----------------
def save_event(data):
    response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=HEADERS, data=json.dumps(data))
    return response.status_code in [200, 201]

def load_events():
    response = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=HEADERS)
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        if not df.empty:
            sort_col = "timestamp" if "timestamp" in df.columns else "id"
            df = df.sort_values(sort_col, ascending=False)
        return df
    return pd.DataFrame()

def button_group(name, options, prefix, active_index=None):
    """Create horizontal buttons with active highlighting."""
    return html.Div(
        [
            html.Label(name, style={"fontWeight": "bold", "marginBottom": "6px"}),
            html.Div(
                [
                    dbc.Button(
                        opt,
                        id={"type": prefix, "index": opt},
                        color="primary" if opt == active_index else "secondary",
                        outline=opt != active_index,
                        className="m-1",
                        n_clicks=0,
                    )
                    for opt in options
                ],
                className="d-flex flex-wrap",
            ),
        ],
        className="my-2",
    )

def last_clicked(clicks, ids):
    """Return the value of the last clicked button in a group."""
    if not clicks or not any(clicks):
        return None
    idx = clicks.index(max(clicks))
    return ids[idx]["index"]

# ---------------- LAYOUT ----------------
app.layout = dbc.Container([
    html.H1("🏐 Volleyball Event Dashboard", className="my-3 text-center"),

    dbc.Row([
        dbc.Col([
            dbc.Label("🎥 YouTube Video URL"),
            dcc.Input(id="video_url", type="text", placeholder="https://www.youtube.com/watch?v=example", style={"width": "100%"}),
            html.Div(id="video_player", className="my-2")
        ], width=6),
        dbc.Col([
            dbc.Label("🏆 Game Name"),
            dcc.Input(id="game_name", type="text", placeholder="e.g. Blich vs Ramat Gan", style={"width": "100%"}),
            dbc.Label("🎯 Set Number"),
            dcc.Dropdown(id="set_number", options=[{"label": s, "value": s} for s in ["", "1st Set", "2nd Set", "3rd Set", "4th Set", "5th Set"]], value="")
        ], width=6)
    ], className="my-3"),

    html.Div(id="player_buttons", children=button_group("🏐 Select Player", PLAYERS, "player")),
    html.Div(id="event_buttons", children=button_group("⚡ Select Event", EVENTS, "event")),
    html.Div(id="subchoice_buttons"),
    html.Div(id="outcome_buttons"),
    html.Div(id="selection_summary", className="my-3 fw-bold"),

    dbc.Button("💾 Save Event", id="save_event", color="success", className="my-3"),
    html.Div(id="save_status"),

    html.Hr(),
    html.H3("Logged Events"),
    html.Div(id="events_table_div"),
    dcc.Interval(id="refresh_table", interval=5000, n_intervals=0)
], fluid=True)

# ---------------- CALLBACKS ----------------

# Video update
@app.callback(
    Output("video_player", "children"),
    Input("video_url", "value")
)
def update_video(url):
    if url:
        return html.Iframe(src=url.replace("watch?v=", "embed/"), width="100%", height="360")
    return ""

# Subchoice buttons (Attack Type / Set To)
@app.callback(
    Output("subchoice_buttons", "children"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    State({"type": "event", "index": ALL}, "id"),
)
def update_subchoice(event_clicks, ids):
    event_selected = last_clicked(event_clicks, ids)
    if event_selected == "Attack":
        return button_group("⚡ Attack Type", ATTACK_TYPES, "attack_type")
    elif event_selected == "Set":
        return button_group("🧱 Set To", SET_TO, "set_to")
    return ""

# Outcome buttons
@app.callback(
    Output("outcome_buttons", "children"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    Input({"type": "attack_type", "index": ALL}, "n_clicks"),
    Input({"type": "set_to", "index": ALL}, "n_clicks"),
    State({"type": "event", "index": ALL}, "id"),
    State({"type": "attack_type", "index": ALL}, "id"),
    State({"type": "set_to", "index": ALL}, "id"),
)
def update_outcome(event_clicks, attack_clicks, set_clicks, event_ids, attack_ids, set_ids):
    event_selected = last_clicked(event_clicks, event_ids)
    attack_selected = last_clicked(attack_clicks, attack_ids)
    set_selected = last_clicked(set_clicks, set_ids)
    
    event = event_selected or (attack_selected and "Attack") or (set_selected and "Set")
    if not event:
        return ""
    
    base_outcomes = EVENT_OUTCOMES.get(event, [])
    if event == "Attack" and attack_selected == "Spike":
        base_outcomes += ["Hard Blocked", "Soft Blocked", "Kill"]
    
    return button_group("🎯 Select Outcome", base_outcomes, "outcome")

# Handle selection summary + save
@app.callback(
    Output("selection_summary", "children"),
    Output("save_status", "children"),
    Input({"type": "player", "index": ALL}, "n_clicks"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    Input({"type": "attack_type", "index": ALL}, "n_clicks"),
    Input({"type": "set_to", "index": ALL}, "n_clicks"),
    Input({"type": "outcome", "index": ALL}, "n_clicks"),
    Input("save_event", "n_clicks"),
    State({"type": "player", "index": ALL}, "id"),
    State({"type": "event", "index": ALL}, "id"),
    State({"type": "attack_type", "index": ALL}, "id"),
    State({"type": "set_to", "index": ALL}, "id"),
    State({"type": "outcome", "index": ALL}, "id"),
    State("video_url", "value"),
    State("game_name", "value"),
    State("set_number", "value"),
    prevent_initial_call=True,
)
def handle_selection(player_clicks, event_clicks, attack_clicks, set_clicks, outcome_clicks,
                     save_click, player_ids, event_ids, attack_ids, set_ids, outcome_ids,
                     video_url, game_name, set_number):
    selected_player = last_clicked(player_clicks, player_ids)
    selected_event = last_clicked(event_clicks, event_ids)
    selected_attack_type = last_clicked(attack_clicks, attack_ids)
    selected_set_to = last_clicked(set_clicks, set_ids)
    selected_outcome = last_clicked(outcome_clicks, outcome_ids)
    
    save_status = ""
    if ctx.triggered_id == "save_event":
        extra = selected_attack_type or selected_set_to
        if selected_player and selected_event and selected_outcome:
            data = {
                "player": selected_player,
                "event": f"{selected_event} ({extra})" if extra else selected_event,
                "outcome": selected_outcome,
                "video_url": video_url,
                "game_name": game_name,
                "set_number": set_number or None,
            }
            success = save_event(data)
            save_status = dbc.Alert("✅ Event saved!" if success else "❌ Failed to save.", 
                                   color="success" if success else "danger")
        else:
            save_status = dbc.Alert("⚠️ Please select all fields before saving.", color="warning")
    
    summary = f"Selected: {selected_player or '–'} | {selected_event or '–'} | {selected_attack_type or selected_set_to or '–'} | {selected_outcome or '–'}"
    return summary, save_status

# Refresh table
@app.callback(
    Output("events_table_div", "children"),
    Input("refresh_table", "n_intervals")
)
def refresh_events_table(n):
    df = load_events()
    if df.empty:
        return html.Div("No events logged yet.")
    df_display = df.drop(columns=["timestamp"], errors="ignore").copy()
    table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df_display.columns],
        data=df_display.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"}
    )
    return table

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080)
