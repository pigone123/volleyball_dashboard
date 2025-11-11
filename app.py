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

# ---------------- HELPER ----------------
def create_button_group(name, options, prefix, selected=None):
    """Create horizontal buttons with highlighting based on selected value."""
    return html.Div(
        [
            html.Label(name, style={"fontWeight": "bold", "marginBottom": "6px"}),
            html.Div(
                [
                    dbc.Button(
                        opt,
                        id={"type": prefix, "index": opt},
                        color="primary" if opt == selected else "secondary",
                        outline=False,
                        className="m-1",
                        n_clicks=0,
                    )
                    for opt in options
                ],
                className="d-flex flex-wrap"
            ),
        ],
        className="my-2",
    )

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

    # Stores for selections
    dcc.Store(id="store_player", data=""),
    dcc.Store(id="store_event", data=""),
    dcc.Store(id="store_attack_type", data=""),
    dcc.Store(id="store_set_to", data=""),
    dcc.Store(id="store_outcome", data=""),

    html.Div(id="player_buttons"),
    html.Div(id="event_buttons"),
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

# Video
@app.callback(Output("video_player", "children"), Input("video_url", "value"))
def update_video(url):
    if url:
        return html.Iframe(src=url.replace("watch?v=", "embed/"), width="100%", height="360")
    return ""

# Render player and event buttons
@app.callback(
    Output("player_buttons", "children"),
    Output("event_buttons", "children"),
    Input("store_player", "data"),
    Input("store_event", "data")
)
def render_buttons(player_sel, event_sel):
    return create_button_group("🏐 Select Player", PLAYERS, "player", player_sel), \
           create_button_group("⚡ Select Event", EVENTS, "event", event_sel)

# Update subchoice buttons based on event selection
@app.callback(
    Output("subchoice_buttons", "children"),
    Input("store_event", "data"),
    Input("store_attack_type", "data"),
    Input("store_set_to", "data")
)
def update_subchoice(event_sel, attack_sel, set_sel):
    if event_sel == "Attack":
        return create_button_group("⚡ Attack Type", ATTACK_TYPES, "attack_type", attack_sel)
    elif event_sel == "Set":
        return create_button_group("🧱 Set To", SET_TO, "set_to", set_sel)
    return ""

# Update outcome buttons
@app.callback(
    Output("outcome_buttons", "children"),
    Input("store_event", "data"),
    Input("store_attack_type", "data"),
    Input("store_set_to", "data"),
    Input("store_outcome", "data")
)
def update_outcome(event_sel, attack_sel, set_sel, outcome_sel):
    if not event_sel:
        return ""
    base_outcomes = EVENT_OUTCOMES.get(event_sel, [])
    if event_sel == "Attack" and attack_sel == "Spike":
        base_outcomes += ["Hard Blocked", "Soft Blocked", "Kill"]
    return create_button_group("🎯 Select Outcome", base_outcomes, "outcome", outcome_sel)

# Handle selections for all groups
@app.callback(
    Output("store_player", "data"),
    Output("store_event", "data"),
    Output("store_attack_type", "data"),
    Output("store_set_to", "data"),
    Output("store_outcome", "data"),
    Input({"type": "player", "index": ALL}, "n_clicks"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    Input({"type": "attack_type", "index": ALL}, "n_clicks"),
    Input({"type": "set_to", "index": ALL}, "n_clicks"),
    Input({"type": "outcome", "index": ALL}, "n_clicks"),
    State("store_player", "data"),
    State("store_event", "data"),
    State("store_attack_type", "data"),
    State("store_set_to", "data"),
    State("store_outcome", "data"),
)
def update_stores(p_clicks, e_clicks, a_clicks, s_clicks, o_clicks,
                  player_sel, event_sel, attack_sel, set_sel, outcome_sel):
    def get_clicked(options, clicks, current):
        for opt, c in zip(options, clicks):
            if c:
                return opt
        return current

    player_sel = get_clicked(PLAYERS, p_clicks, player_sel)
    event_sel = get_clicked(EVENTS, e_clicks, event_sel)
    attack_sel = get_clicked(ATTACK_TYPES, a_clicks, attack_sel)
    set_sel = get_clicked(SET_TO, s_clicks, set_sel)
    outcome_sel = get_clicked(EVENT_OUTCOMES.get(event_sel, []), o_clicks, outcome_sel)

    return player_sel, event_sel, attack_sel, set_sel, outcome_sel

# Save event
@app.callback(
    Output("save_status", "children"),
    Output("selection_summary", "children"),
    Input("save_event", "n_clicks"),
    State("store_player", "data"),
    State("store_event", "data"),
    State("store_attack_type", "data"),
    State("store_set_to", "data"),
    State("store_outcome", "data"),
    State("video_url", "value"),
    State("game_name", "value"),
    State("set_number", "value"),
    prevent_initial_call=True
)
def save_event_callback(n, player_sel, event_sel, attack_sel, set_sel, outcome_sel, video_url, game_name, set_number):
    extra = attack_sel or set_sel
    summary = f"Selected: {player_sel or '–'} | {event_sel or '–'} | {extra or '–'} | {outcome_sel or '–'}"
    if player_sel and event_sel and outcome_sel:
        data = {
            "player": player_sel,
            "event": f"{event_sel} ({extra})" if extra else event_sel,
            "outcome": outcome_sel,
            "video_url": video_url,
            "game_name": game_name,
            "set_number": set_number if set_number else None
        }
        success = save_event(data)
        if success:
            return dbc.Alert("✅ Event saved!", color="success"), summary
        return dbc.Alert("❌ Failed to save.", color="danger"), summary
    return dbc.Alert("⚠️ Please select all fields before saving.", color="warning"), summary

# Refresh logged events table
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
