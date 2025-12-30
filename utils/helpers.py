import streamlit as st

def horizontal_radio(label, options, session_key):
    current = st.session_state.get(session_key, options[0])
    return st.radio(
        label,
        options,
        index=options.index(current) if current in options else 0,
        horizontal=True,
        key=session_key
    )

def extract_category(event_value):
    return event_value.split("(")[0].strip() if "(" in event_value else event_value
