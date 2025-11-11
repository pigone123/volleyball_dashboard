# app.py
import os
import json
import requests
import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output, State, ctx
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
PLAYERS = ["", "Ori", "Ofir", "Beni", "Hillel", "Shak", "Omer Saar", "Omer", "Karat", "Lior", "Yonatan", "Ido", "Royi"]
EVENTS = ["", "Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"]
ATTACK_TYPES = ["", "Free Ball", "Tip", "Hole", "Spike"]
SET_TO = ["", "Position 1", "Position 2", "Position 3", "Position 4", "Position 6"]

EVENT_OUTCOMES = {
    "Serve": ["Ace", "Out", "Net", "In", "Off System"],
    "Attack": ["Blockout", "Out", "Net", "In Play", "Off System"],
    "Block": ["Blockout", "Touch", "Kill", "Softblock", "Error"],
    "Receive": ["Good", "Neutral", "Bad"],
    "Dig": ["Good", "Neutral", "Bad"],
    "Set": ["0 Blockers", "1 Blocker", "2 Blocker"],
    "Defense": ["Good", "Neutral", "Bad"]
}

# ---------------- FUNCTIONS ----------------
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

def update_event(row_id, updated_data):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(updated_data))
    return response.status_code in [200, 204]

def delete_event(row_id):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code in [200, 204]

# ---------------- LAYOUT ----------------
app.layout = dbc.Container([
    html.H1("🏐 Volleyball Event Dashboard", className="my-3"),

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

    dbc.Row([
        dbc.Col([
            dbc.Label("🏐 Select Player"),
            dcc.RadioItems(id="selected_player", options=[{"label": p, "value": p} for p in PLAYERS], value="")
        ], width=4),
        dbc.Col([
            dbc.Label("⚡ Select Event"),
            dcc.RadioItems(id="selected_event", options=[{"label": e, "value": e} for e in EVENTS], value="")
        ], width=4),
        dbc.Col([
            dbc.Label("⚡ Attack Type / 🧱 Set To"),
            dcc.RadioItems(id="sub_choice", options=[], value="")
        ], width=4),
    ], className="my-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("🎯 Select Outcome"),
            dcc.RadioItems(id="selected_outcome", options=[], value="")
        ])
    ], className="my-3"),

    dbc.Row([
        dbc.Col(dbc.Button("💾 Save Event", id="save_event", color="success"), width=2),
        dbc.Col(html.Div(id="save_status"), width=10)
    ], className="my-3"),

    html.Hr(),

    html.H3("Logged Events"),
    html.Div(id="events_table_div"),
    dcc.Interval(id="refresh_table", interval=5000, n_intervals=0)  # refresh table every 5s
], fluid=True)

# ---------------- CALLBACKS ----------------
@app.callback(
    Output("video_player", "children"),
    Input("video_url", "value")
)
def update_video(url):
    if url:
        return html.Iframe(src=url.replace("watch?v=", "embed/"), width="100%", height="360")
    return ""

@app.callback(
    Output("sub_choice", "options"),
    Output("sub_choice", "value"),
    Output("selected_outcome", "options"),
    Output("selected_outcome", "value"),
    Input("selected_event", "value"),
    Input("sub_choice", "value")
)
def update_sub_choices(event, sub_choice_value):
    attack_type_opts = [{"label": a, "value": a} for a in ATTACK_TYPES] if event == "Attack" else []
    set_to_opts = [{"label": s, "value": s} for s in SET_TO] if event == "Set" else []
    options = attack_type_opts + set_to_opts
    sub_choice_val = options[0]["value"] if options else ""
    
    # Outcome options
    base_outcomes = EVENT_OUTCOMES.get(event, [])
    if event == "Attack" and sub_choice_value == "Spike":
        base_outcomes += ["Hard Blocked", "Soft Blocked", "Kill"]
    outcome_options = [{"label": o, "value": o} for o in [""] + base_outcomes] if base_outcomes else []
    outcome_val = outcome_options[0]["value"] if outcome_options else ""
    
    return options, sub_choice_val, outcome_options, outcome_val

@app.callback(
    Output("save_status", "children"),
    Input("save_event", "n_clicks"),
    State("selected_player", "value"),
    State("selected_event", "value"),
    State("sub_choice", "value"),
    State("selected_outcome", "value"),
    State("video_url", "value"),
    State("game_name", "value"),
    State("set_number", "value"),
    prevent_initial_call=True
)
def save_event_callback(n_clicks, player, event, sub_choice, outcome, video_url, game_name, set_number):
    if player and event and outcome:
        extra_info = sub_choice
        data = {
            "player": player,
            "event": f"{event} ({extra_info})" if extra_info else event,
            "outcome": outcome,
            "video_url": video_url,
            "game_name": game_name,
            "set_number": set_number if set_number else None
        }
        success = save_event(data)
        if success:
            return dbc.Alert(f"✅ Saved: {player} | {event} | {extra_info if extra_info else ''} | {outcome}", color="success")
        return dbc.Alert("❌ Failed to save", color="danger")
    return dbc.Alert("⚠️ Please select player, event, and outcome", color="warning")

@app.callback(
    Output("events_table_div", "children"),
    Input("refresh_table", "n_intervals")
)
def refresh_events_table(n):
    df = load_events()
    if df.empty:
        return html.Div("No events logged yet.")
    # Add delete checkboxes
    df_display = df.drop(columns=["timestamp"], errors="ignore").copy()
    df_display["Delete?"] = False
    table = dash_table.DataTable(
        columns=[{"name": c, "id": c, "editable": c not in ["id"]} for c in df_display.columns],
        data=df_display.to_dict("records"),
        row_deletable=True,
        editable=True,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"}
    )
    return table

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_server(debug=True)
