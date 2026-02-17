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

# @st.cache_data(ttl=60)
def load_events():
    all_rows = []
    start = 0
    batch_size = 1000

    while True:
        headers = {
            **HEADERS,
            "Range": f"{start}-{start + batch_size - 1}"
        }

        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*&order=id.desc",
            headers=headers
        )

        if r.status_code != 200:
            st.error(r.text)
            break

        data = r.json()
        if not data:
            break

        all_rows.extend(data)
        start += batch_size

    return pd.DataFrame(all_rows)


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




