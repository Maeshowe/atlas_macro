"""
ATLAS MACRO - History Chart Component

State timeline with colored markers per day.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STATE_COLORS = {"CALM": "#22c55e", "STRESSED": "#eab308", "CRISIS": "#ef4444"}
STATE_Y = {"CALM": 0, "STRESSED": 1, "CRISIS": 2}


def render_history_chart(history: pd.DataFrame) -> None:
    """Render historical state timeline with colored markers."""
    fig = go.Figure()

    for state, color in STATE_COLORS.items():
        mask = history["macro_state"] == state
        subset = history[mask]
        if not subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=subset["date"].astype(str),
                    y=[STATE_Y[state]] * len(subset),
                    mode="markers",
                    name=state,
                    marker=dict(color=color, size=12, symbol="square"),
                )
            )

    fig.update_layout(
        yaxis=dict(
            tickvals=[0, 1, 2],
            ticktext=["CALM", "STRESSED", "CRISIS"],
            range=[-0.5, 2.5],
        ),
        xaxis_title="Date",
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)
