import json
import requests
import pandas as pd
from config.supabase import SUPABASE_URL, TABLE_NAME, HEADERS
import streamlit as st

def save_event(data):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        headers=HEADERS,
        data=json.dumps(data)
    )
    if r.status_code not in (200, 201):
        st.error(res.text)
    return r

@st.cache_data(ttl=60)
def load_events():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*",
        headers=HEADERS
    )
    if r.status_code == 200:
        return pd.DataFrame(r.json())
    return pd.DataFrame()

def update_event(row_id, updated_data):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}",
        headers=HEADERS,
        data=json.dumps(updated_data)
    )

def delete_event(row_id):
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{row_id}",
        headers=HEADERS
    )


