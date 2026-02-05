"""
ATLAS MACRO - State Indicator Component

Semicircular gauge showing CALM / STRESSED / CRISIS state.
"""

import plotly.graph_objects as go
import streamlit as st

STATE_COLORS = {
    "CALM": "#22c55e",
    "STRESSED": "#eab308",
    "CRISIS": "#ef4444",
}

STATE_VALUES = {"CALM": 16.7, "STRESSED": 50.0, "CRISIS": 83.3}


def render_state_indicator(state: str, confidence: str, date_str: str) -> None:
    """Render semicircular gauge for macro state."""
    value = STATE_VALUES.get(state, 50.0)
    color = STATE_COLORS.get(state, "#6b7280")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"font": {"size": 1, "color": "rgba(0,0,0,0)"}},
            title={"text": f"ATLAS MACRO - {date_str}", "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100], "visible": False},
                "bar": {"color": "rgba(0,0,0,0)"},
                "bgcolor": "#f3f4f6",
                "steps": [
                    {"range": [0, 33.3], "color": "#22c55e"},
                    {"range": [33.3, 66.7], "color": "#eab308"},
                    {"range": [66.7, 100], "color": "#ef4444"},
                ],
                "threshold": {
                    "line": {"color": "#1f2937", "width": 4},
                    "thickness": 0.8,
                    "value": value,
                },
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin=dict(l=20, r=20, t=50, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"<h2 style='text-align:center; color:{color};'>{state}</h2>"
        f"<p style='text-align:center; color:#6b7280;'>Confidence: {confidence}</p>",
        unsafe_allow_html=True,
    )
