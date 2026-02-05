"""
ATLAS MACRO Streamlit Dashboard.

Run with: streamlit run src/atlas_macro/dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure atlas_macro is importable when run via `streamlit run`
_SRC_DIR = str(Path(__file__).resolve().parents[2])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import json

import streamlit as st

from atlas_macro.dashboard.components.driver_panel import render_driver_panel
from atlas_macro.dashboard.components.history_chart import render_history_chart
from atlas_macro.dashboard.components.metric_cards import render_metric_cards
from atlas_macro.dashboard.components.state_indicator import render_state_indicator
from atlas_macro.pipeline.daily import DailyPipeline


def main() -> None:
    st.set_page_config(
        page_title="ATLAS MACRO",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("ATLAS MACRO")
    st.markdown("**Macro-Level Market Constraint & Stress Diagnostic**")

    # Sidebar
    with st.sidebar:
        st.header("About ATLAS MACRO")
        st.markdown(
            """
            ATLAS answers: *Are there macro-level conditions that
            constrain or override otherwise valid market signals?*

            **States:**
            - **CALM**: Normal conditions
            - **STRESSED**: Elevated volatility or rate pressure
            - **CRISIS**: Extreme stress, correlation spike

            **Design:**
            - Macro is a constraint, not a driver
            - No forecasting, no narratives
            - Deterministic, rule-based
            - Discrete states only (no scores)
            """
        )

        st.divider()

        st.markdown(
            """
            **Data Sources:**
            - VIX: Polygon (I:VIX), FRED fallback
            - Rates: FRED (DGS10, T10Y2Y)
            - Credit: FRED (BAMLH0A0HYM2)
            - Correlation: Polygon (SPY/QQQ/IWM/DIA)
            """
        )

    # Load data
    pipeline = DailyPipeline()
    history = pipeline.get_history()

    if history.empty:
        st.warning(
            "No historical data. Run the pipeline first:\n"
            "```\npython scripts/run_daily.py\n```"
        )
        return

    latest = history.iloc[-1]

    # Row 1: State indicator + Driver panel
    col1, col2 = st.columns([1, 2])
    with col1:
        render_state_indicator(
            state=latest["macro_state"],
            confidence=latest["confidence"],
            date_str=str(latest["date"]),
        )
    with col2:
        drivers = (
            json.loads(latest["drivers"])
            if isinstance(latest["drivers"], str)
            else latest["drivers"]
        )
        render_driver_panel(drivers)

    # Row 2: Metric cards
    st.markdown("### Stress Metrics")
    render_metric_cards(latest)

    # Row 3: History chart
    st.markdown("### State History")
    if len(history) > 1:
        render_history_chart(history)
    else:
        st.info("Need more data points for history chart.")

    # Raw data expander
    with st.expander("Raw Data"):
        st.dataframe(history.tail(20))


if __name__ == "__main__":
    main()
