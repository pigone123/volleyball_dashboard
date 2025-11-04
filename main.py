import streamlit as st

def button_style_row(options, session_key, color):
    cols = st.columns(len(options), gap="small")
    for i, option in enumerate(options):
        selected = st.session_state.get(session_key) == option
        bg_color = color if selected else "#F0F2F6"
        fg_color = "white" if selected else "black"

        if cols[i].button(option, key=f"{session_key}_{option}"):
            st.session_state[session_key] = option

        # Apply color immediately (works for Streamlit >=1.22)
        cols[i].markdown(
            f"""
            <style>
            div.stButton>button[key="{session_key}_{option}"] {{
                background-color: {bg_color} !important;
                color: {fg_color} !important;
                border-radius: 6px;
                padding: 0.3em 0.6em;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Example usage:
st.title("Test Button Highlighting")

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

players = ["Ori","Ofir","Beni","Hillel"]
button_style_row(players, "selected_player", "#4CAF50")

st.write("Selected player:", st.session_state.selected_player)
