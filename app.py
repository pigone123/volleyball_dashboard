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

# ---------------- HELPER COMPONENTS ----------------
def create_button_group(name, options, prefix):
    """Creates a horizontal button group for selections."""
    return html.Div(
        [
            html.Label(name, style={"fontWeight": "bold", "marginBottom": "6px"}),
            html.Div(
                [
                    dbc.Button(
                        opt,
                        id={"type": prefix, "index": opt},
                        color="secondary",
                        outline=True,
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

    create_button_group("🏐 Select Player", PLAYERS, "player"),
    create_button_group("⚡ Select Event", EVENTS, "event"),
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
@app.callback(
    Output("video_player", "children"),
    Input("video_url", "value")
)
def update_video(url):
    if url:
        return html.Iframe(src=url.replace("watch?v=", "embed/"), width="100%", height="360")
    return ""

# Update subchoice buttons based on event selection
@app.callback(
    Output("subchoice_buttons", "children"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_subchoice(event_clicks):
    ctx_id = ctx.triggered_id
    if not ctx_id:
        return ""
    event_selected = ctx_id["index"]
    if event_selected == "Attack":
        return create_button_group("⚡ Attack Type", ATTACK_TYPES, "attack_type")
    elif event_selected == "Set":
        return create_button_group("🧱 Set To", SET_TO, "set_to")
    return ""

# Update outcome buttons based on event/attack_type selection
@app.callback(
    Output("outcome_buttons", "children"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    Input({"type": "attack_type", "index": ALL}, "n_clicks"),
    Input({"type": "set_to", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_outcome(event_clicks, attack_clicks, set_clicks):
    triggered = ctx.triggered_id
    event_selected = triggered["index"] if triggered and triggered["type"] == "event" else None
    attack_selected = triggered["index"] if triggered and triggered["type"] == "attack_type" else None
    set_selected = triggered["index"] if triggered and triggered["type"] == "set_to" else None

    event = event_selected or ("Attack" if attack_selected else "Set" if set_selected else None)
    if not event:
        return ""
    base_outcomes = EVENT_OUTCOMES.get(event, [])
    if event == "Attack" and attack_selected == "Spike":
        base_outcomes += ["Hard Blocked", "Soft Blocked", "Kill"]
    return create_button_group("🎯 Select Outcome", base_outcomes, "outcome")

# Highlight clicked buttons in each group
@app.callback(
    Output({"type": "player", "index": ALL}, "color"),
    Output({"type": "event", "index": ALL}, "color"),
    Output({"type": "attack_type", "index": ALL}, "color"),
    Output({"type": "set_to", "index": ALL}, "color"),
    Output({"type": "outcome", "index": ALL}, "color"),
    Input({"type": "player", "index": ALL}, "n_clicks"),
    Input({"type": "event", "index": ALL}, "n_clicks"),
    Input({"type": "attack_type", "index": ALL}, "n_clicks"),
    Input({"type": "set_to", "index": ALL}, "n_clicks"),
    Input({"type": "outcome", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_button_colors(player_clicks, event_clicks, attack_clicks, set_clicks, outcome_clicks):
    def highlight_group(clicks):
        if not clicks:
            return []
        max_idx = max((i for i, c in enumerate(clicks) if c), default=None)
        return ["primary" if i == max_idx else "secondary" for i in range(len(clicks))]

    return (
        highlight_group(player_clicks),
        highlight_group(event_clicks),
        highlight_group(attack_clicks),
        highlight_group(set_clicks),
        highlight_group(outcome_clicks)
    )

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
    State("video_url", "value"),
    State("game_name", "value"),
    State("set_number", "value"),
    prevent_initial_call=True
)
def handle_selection(players, events, attack_types, set_tos, outcomes, save_click, video_url, game_name, set_number):
    triggered = ctx.triggered_id
    save_status = ""

    selected_player = next((btn["index"] for btn, c in zip(ctx.inputs_list[0], players) if c), "")
    selected_event = next((btn["index"] for btn, c in zip(ctx.inputs_list[1], events) if c), "")
    selected_attack_type = next((btn["index"] for btn, c in zip(ctx.inputs_list[2], attack_types) if c), "")
    selected_set_to = next((btn["index"] for btn, c in zip(ctx.inputs_list[3], set_tos) if c), "")
    selected_outcome = next((btn["index"] for btn, c in zip(ctx.inputs_list[4], outcomes) if c), "")

    if triggered == "save_event":
        event = selected_event
        extra = selected_attack_type or selected_set_to
        if selected_player and event and selected_outcome:
            data = {
                "player": selected_player,
                "event": f"{event} ({extra})" if extra else event,
                "outcome": selected_outcome,
                "video_url": video_url,
                "game_name": game_name,
                "set_number": set_number if set_number else None
            }
            success = save_event(data)
            if success:
                save_status = dbc.Alert("✅ Event saved!", color="success")
            else:
                save_status = dbc.Alert("❌ Failed to save.", color="danger")
        else:
            save_status = dbc.Alert("⚠️ Please select all fields before saving.", color="warning")

    summary = f"Selected: {selected_player or '–'} | {selected_event or '–'} | {selected_attack_type or selected_set_to or '–'} | {selected_outcome or '–'}"
    return summary, save_status

# Refresh events table
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
