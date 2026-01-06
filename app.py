# import os
# import json
# import requests
# import pandas as pd
# from dash import Dash, dcc, html, dash_table, ctx
# from dash.dependencies import Input, Output, State, ALL
# import dash_bootstrap_components as dbc

# # ---------------- SUPABASE CONFIG ----------------
# SUPABASE_URL = os.environ.get("SUPABASE_URL")
# SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# TABLE_NAME = "Volleyball_events"

# HEADERS = {
#     "apikey": SUPABASE_KEY,
#     "Authorization": f"Bearer {SUPABASE_KEY}",
#     "Content-Type": "application/json"
# }

# # ---------------- DASH APP ----------------
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# server = app.server

# # ---------------- CONSTANTS ----------------
# PLAYERS = ["Ori", "Ofir", "Beni", "Hillel", "Shak", "Omer Saar", "Omer", "Karat", "Lior", "Yonatan", "Ido", "Royi"]
# EVENTS = ["Serve", "Attack", "Block", "Receive", "Dig", "Set", "Defense"]
# ATTACK_TYPES = ["Free Ball", "Tip", "Hole", "Spike"]
# SET_TO = ["Position 1", "Position 2", "Position 3", "Position 4", "Position 6"]

# EVENT_OUTCOMES = {
#     "Serve": ["Ace", "Out", "Net", "In", "Off System"],
#     "Attack": ["Blockout", "Out", "Net", "In Play", "Off System"],
#     "Block": ["Blockout", "Touch", "Kill", "Softblock", "Error"],
#     "Receive": ["Good", "Neutral", "Bad"],
#     "Dig": ["Good", "Neutral", "Bad"],
#     "Set": ["0 Blockers", "1 Blocker", "2 Blocker"],
#     "Defense": ["Good", "Neutral", "Bad","Overpass", "Error"]
# }

# # ---------------- HELPERS ----------------
# def create_button_group(name, options, prefix, selected_value=None):
#     return html.Div([
#         html.Label(name, style={"fontWeight": "bold", "marginBottom": "6px"}),
#         html.Div([
#             dbc.Button(
#                 opt,
#                 id={"type": prefix, "index": opt},
#                 color="success" if opt == selected_value else "primary",
#                 outline=opt != selected_value,
#                 className="m-1 selectable-btn",
#                 n_clicks=0
#             ) for opt in options
#         ], className="d-flex flex-wrap justify-content-center")
#     ], className="my-2")

# def save_event(data):
#     response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=HEADERS, data=json.dumps(data))
#     return response.status_code in [200, 201]

# def load_events():
#     response = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=HEADERS)
#     if response.status_code == 200:
#         df = pd.DataFrame(response.json())
#         if not df.empty:
#             df = df.sort_values("id", ascending=False)
#         return df
#     return pd.DataFrame()

# def update_event(row_id, updated_data):
#     url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
#     response = requests.patch(url, headers=HEADERS, data=json.dumps(updated_data))
#     return response.status_code in [200, 204]

# def delete_event(row_id):
#     url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}"
#     response = requests.delete(url, headers=HEADERS)
#     return response.status_code in [200, 204]

# # ---------------- LAYOUT ----------------
# app.layout = dbc.Container([
#     html.H1("🏐 Volleyball Event Dashboard", className="my-3 text-center"),

#     dbc.Row([
#         dbc.Col([
#             dbc.Label("🎥 YouTube Video URL"),
#             dcc.Input(id="video_url", type="text", placeholder="https://www.youtube.com/watch?v=example", style={"width": "100%"}),
#             html.Div(id="video_player", className="my-2")
#         ], width=6),
#         dbc.Col([
#             dbc.Label("🏆 Game Name"),
#             dcc.Input(id="game_name", type="text", placeholder="e.g. Blich vs Ramat Gan", style={"width": "100%"}),
#             dbc.Label("🎯 Set Number"),
#             dcc.Dropdown(
#                 id="set_number",
#                 options=[{"label": s, "value": s} for s in ["", "1st Set", "2nd Set", "3rd Set", "4th Set", "5th Set"]],
#                 value=""
#             )
#         ], width=6)
#     ], className="my-3"),

#     create_button_group("🏐 Select Player", PLAYERS, "player"),
#     create_button_group("⚡ Select Event", EVENTS, "event"),
#     html.Div(id="subchoice_buttons"),
#     html.Div(id="outcome_buttons"),
#     html.Div(id="selection_summary", className="my-3 fw-bold text-center"),
#     dbc.Button("💾 Save Event", id="save_event", color="success", className="my-3 d-block mx-auto"),
#     html.Div(id="save_status"),

#     html.Hr(),
#     html.H3("📋 Logged Events", className="text-center my-3"),
#     html.Div(id="filters-container", className="d-flex justify-content-center flex-wrap gap-3 my-2"),
#     html.Div(id="events_table_div", className="mb-3"),
#     dbc.Button("💾 Save Changes", id="save_table_changes", color="primary", className="my-3 d-block mx-auto"),
#     html.Div(id="table_save_status", className="text-center mb-4")
# ], fluid=True)

# # ---------------- CALLBACKS ----------------
# @app.callback(Output("video_player", "children"), Input("video_url", "value"))
# def update_video(url):
#     if url:
#         return html.Iframe(src=url.replace("watch?v=", "embed/"), width="100%", height="360")
#     return ""

# # --- button highlight fix ---
# @app.callback(
#     Output("selection_summary", "children"),
#     Input({"type": "player", "index": ALL}, "n_clicks"),
#     Input({"type": "event", "index": ALL}, "n_clicks"),
#     Input({"type": "attack_type", "index": ALL}, "n_clicks"),
#     Input({"type": "set_to", "index": ALL}, "n_clicks"),
#     Input({"type": "outcome", "index": ALL}, "n_clicks"),
#     prevent_initial_call=False
# )
# def handle_selection(players, events, attack_types, set_tos, outcomes):
#     selected = {"Player": None, "Event": None, "Attack Type": None, "Set To": None, "Outcome": None}
#     for group_name, group_clicks, group_type in [
#         ("Player", players, "player"),
#         ("Event", events, "event"),
#         ("Attack Type", attack_types, "attack_type"),
#         ("Set To", set_tos, "set_to"),
#         ("Outcome", outcomes, "outcome")
#     ]:
#         if any(group_clicks):
#             i = group_clicks.index(max(group_clicks))
#             try:
#                 btn_id = list(ctx.inputs.keys())[i][1]["index"]
#                 selected[group_name] = btn_id
#             except Exception:
#                 pass

#     summary = " | ".join([f"{k}: {v}" for k, v in selected.items() if v])
#     return f"Selected: {summary or '–'}"

# # ---------------- Table Refresh ----------------
# @app.callback(
#     Output("events_table_div", "children"),
#     Input("refresh_table_btn", "n_clicks"),
#     Input("save_event", "n_clicks"),  # refresh when new event saved
# )
# def refresh_table(_, __):
#     df = load_events()
#     if df.empty:
#         return html.Div("No events logged yet.")

#     # Build dropdown filters dynamically for each column except 'id'
#     dropdowns = html.Div(
#         [
#             dcc.Dropdown(
#                 id={"type": "filter-dropdown", "index": col},
#                 options=[{"label": str(v), "value": v} for v in sorted(df[col].dropna().unique())],
#                 placeholder=f"Filter {col}",
#                 style={"width": "150px", "margin": "2px"},
#                 clearable=True
#             )
#             for col in df.columns if col != "id"
#         ],
#         className="d-flex flex-wrap justify-content-center mb-2"
#     )

#     # Build DataTable without "delete" column
#     table = dash_table.DataTable(
#         id="events_table",
#         columns=[{"name": c, "id": c, "editable": c != "id"} for c in df.columns if c != "delete"],
#         data=df.to_dict("records"),
#         editable=True,
#         row_deletable=True,
#         style_table={"overflowY": "auto", "maxHeight": "400px"},
#         style_cell={"textAlign": "left", "minWidth": "100px", "width": "150px"},
#         page_action="none"
#     )

#     return html.Div([
#         dropdowns,
#         table,
#         html.Div(
#             dbc.Button("💾 Save Changes", id="save_table_changes", color="primary", className="my-3"),
#             style={"textAlign": "center"}
#         ),
#         html.Div(id="table_save_status")
#     ])


# # ---------------- Apply Filters ----------------
# @app.callback(
#     Output("events_table", "data"),
#     Input({"type": "filter-dropdown", "index": ALL}, "value")
# )
# def apply_filters(selected_values):
#     df = load_events()
#     filter_columns = [col for col in df.columns if col != "id"]
    
#     for col, selected in zip(filter_columns, selected_values):
#         if selected:
#             df = df[df[col] == selected]
    
#     return df.to_dict("records")

# # ---------------- Save Changes Button ----------------
# @app.callback(
#     Output("table_save_status", "children"),
#     Input("save_table_changes", "n_clicks"),
#     State("events_table", "data"),
#     State("events_table", "data_previous"),
#     prevent_initial_call=True
# )
# def save_table_changes(n_clicks, current_data, previous_data):
#     if not current_data:
#         return dbc.Alert("No data to save.", color="warning")

#     messages = []

#     # Detect deleted rows
#     previous_ids = {row["id"] for row in (previous_data or []) if "id" in row}
#     current_ids = {row["id"] for row in current_data if "id" in row}
#     deleted_ids = previous_ids - current_ids

#     for row_id in deleted_ids:
#         success = delete_event(row_id)
#         messages.append(f"Row {row_id} deleted." if success else f"❌ Failed to delete row {row_id}.")

#     # Detect updated rows
#     for row in current_data:
#         row_id = row.get("id")
#         if not row_id:
#             continue
#         old_row = next((r for r in (previous_data or []) if r.get("id") == row_id), {})
#         updates = {k: v for k, v in row.items() if k not in ["id"] and v != old_row.get(k)}
#         if updates:
#             success = update_event(row_id, updates)
#             messages.append(f"Row {row_id} updated." if success else f"❌ Failed to update row {row_id}.")

#     if not messages:
#         return dbc.Alert("No changes detected.", color="secondary")
#     return dbc.Alert(" | ".join(messages), color="info")


# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     app.run_server(debug=True, host="0.0.0.0", port=8080)
