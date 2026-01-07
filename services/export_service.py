import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

import streamlit as st

from utils.helpers import extract_category
from utils.constants import OUTCOME_ORDER


from utils.helpers import extract_category
from utils.constants import OUTCOME_ORDER

def export_player_excel(df: pd.DataFrame, player_name: str):
    player_df = _prepare_player_df(df, player_name)
    if player_df is None:
        return

    output_path = f"/tmp/{player_name}_volleyball_report.xlsx"
    overall_summary = []

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for category in sorted(player_df["category"].unique()):
            cat_df = player_df[player_df["category"] == category]
            sheet_name = category[:31]

            outcome_stats = _build_outcome_stats(cat_df, category)
            _write_outcome_table(writer, sheet_name, outcome_stats)

            startrow = len(outcome_stats) + 3
            _write_game_table(writer, sheet_name, cat_df, category, startrow)

            _add_category_chart(writer, sheet_name, cat_df, category, startrow)

            _auto_adjust_columns(writer, sheet_name)

            overall_summary.extend(
                _collect_summary_rows(category, outcome_stats)
            )

        _write_summary_sheet(writer, overall_summary)

    _download_excel(output_path, player_name)

def _prepare_player_df(df, player_name):
    player_df = df[df["player"] == player_name].copy()
    if player_df.empty:
        st.error("No data for this player.")
        return None

    player_df["category"] = player_df["event"].apply(extract_category)
    return player_df    

def _build_outcome_stats(cat_df, category):
    stats = cat_df.groupby("outcome").size().reset_index(name="count")
    total = stats["count"].sum()
    stats["percentage"] = (stats["count"] / total * 100).round(1)
    stats.loc[len(stats)] = ["TOTAL", total, 100.0]

    if category in OUTCOME_ORDER:
        stats["order"] = stats["outcome"].apply(
            lambda x: OUTCOME_ORDER[category].index(x)
            if x in OUTCOME_ORDER[category] else 999
        )
        stats = stats.sort_values("order").drop(columns="order")
    else:
        stats = stats.sort_values("count", ascending=False)

    return stats

def _write_outcome_table(writer, sheet, stats):
    stats.to_excel(writer, sheet_name=sheet, index=False)


def _write_game_table(writer, sheet, cat_df, category, startrow):
    if "game_name" not in cat_df.columns:
        return

    game_stats = (
        cat_df.groupby(["game_name", "outcome"])
        .size()
        .reset_index(name="count")
    )

    pivot = game_stats.pivot(
        index="game_name",
        columns="outcome",
        values="count"
    ).fillna(0)

    # Order outcome columns if defined
    if category in OUTCOME_ORDER:
        ordered = [c for c in OUTCOME_ORDER[category] if c in pivot.columns]
        pivot = pivot[ordered + [c for c in pivot.columns if c not in ordered]]

    # ✅ ADD TOTAL PER GAME
    pivot["TOTAL"] = pivot.sum(axis=1)

    pivot.to_excel(writer, sheet_name=sheet, startrow=startrow)



def _add_category_chart(writer, sheet, cat_df, category, startrow):
    ws = writer.book[sheet]

    percent_df = (
        cat_df.groupby(["game_name", "outcome"])
        .size()
        .reset_index(name="count")
    )

    totals = percent_df.groupby("game_name")["count"].sum().reset_index()
    percent_df = percent_df.merge(totals, on="game_name", suffixes=("", "_total"))
    percent_df["percentage"] = (
        percent_df["count"] / percent_df["count_total"] * 100
    ).round(1)

    pivot = percent_df.pivot(
        index="game_name", columns="outcome", values="percentage"
    ).fillna(0)

    if category in OUTCOME_ORDER:
        ordered = [c for c in OUTCOME_ORDER[category] if c in pivot.columns]
        pivot = pivot[ordered + [c for c in pivot.columns if c not in ordered]]

    fig, ax = plt.subplots(figsize=(10, 4))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker="o", label=col)

    ax.set_title(f"{category} Performance (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, dpi=150)
    plt.close(fig)
    img.seek(0)

    xl_img = XLImage(img)
    xl_img.anchor = f"A{startrow + len(pivot) + 5}"
    ws.add_image(xl_img)


def _collect_summary_rows(category, stats):
    return [
        {
            "Category": category,
            "Outcome": row["outcome"],
            "Count": row["count"],
            "Percentage": row["percentage"],
        }
        for _, row in stats.iterrows()
        if row["outcome"] != "TOTAL"
    ]


def _auto_adjust_columns(writer, sheet):
    ws = writer.sheets[sheet]
    for col in ws.columns:
        width = max(len(str(cell.value)) for cell in col if cell.value) + 2
        ws.column_dimensions[get_column_letter(col[0].column)].width = width


def _download_excel(path, player):
    st.success("✅ Excel report created!")
    with open(path, "rb") as f:
        st.download_button(
            "⬇️ Download Excel",
            f,
            file_name=f"{player}_volleyball_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def export_all_events_excel(df):
    output_path = "/tmp/volleyball_events.xlsx"
    df.to_excel(output_path, index=False)

    with open(output_path, "rb") as f:
        st.download_button(
            "⬇️ Download All Events (Excel)",
            f,
            file_name="volleyball_events.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

def _write_summary_sheet(writer, rows):
    df = pd.DataFrame(rows)
    start = 0

    for category in df["Category"].unique():
        sub = df[df["Category"] == category].copy()
        total = sub["Count"].sum()
        sub.loc[len(sub)] = ["TOTAL", "", total, 100.0]

        sub.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
            startrow=start
        )
        start += len(sub) + 3


