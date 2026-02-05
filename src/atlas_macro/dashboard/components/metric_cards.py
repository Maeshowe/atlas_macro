"""
ATLAS MACRO - Metric Cards Component

Displays 5 individual stress metric cards in a row.
"""

import streamlit as st

STRESS_COLORS = {0: "#22c55e", 1: "#eab308", 2: "#ef4444"}
STRESS_LABELS = {0: "CALM", 1: "STRESSED", 2: "CRISIS"}


def render_metric_cards(latest: dict) -> None:
    """Render individual metric stress cards."""
    cols = st.columns(5)

    def _fmt(val: object, fmt: str = ".1f") -> str:
        if val is None or (isinstance(val, float) and val != val):
            return "N/A"
        try:
            return f"{float(val):{fmt}}"
        except (ValueError, TypeError):
            return "N/A"

    metrics = [
        (
            "Volatility",
            int(latest.get("vol_stress", 0)),
            f"VIX: {_fmt(latest.get('vix_level'))}",
            f"Percentile: {_fmt(latest.get('vix_percentile'), '.0f')}",
        ),
        (
            "Rate Stress",
            int(latest.get("rate_stress", 0)),
            f"TNX vs SMA20: {_fmt(latest.get('tnx_vs_sma20'), '+.3f')}",
            "Above SMA" if latest.get("rate_stress", 0) else "Below SMA",
        ),
        (
            "Yield Curve",
            int(latest.get("yield_curve_stress", 0)),
            f"10Y-2Y: {_fmt(latest.get('yield_curve_spread'), '+.2f')}",
            "Inverted" if latest.get("yield_curve_stress", 0) else "Normal",
        ),
        (
            "Credit Spread",
            int(latest.get("credit_stress", 0)),
            f"HY: {_fmt(latest.get('credit_spread'))}",
            "Elevated" if latest.get("credit_stress", 0) else "Normal",
        ),
        (
            "Correlation",
            int(latest.get("correlation_stress", 0)),
            f"Mean: {_fmt(latest.get('mean_pairwise_corr'), '.3f')}",
            "Elevated" if latest.get("correlation_stress", 0) else "Normal",
        ),
    ]

    for i, (name, stress_level, line1, line2) in enumerate(metrics):
        with cols[i]:
            color = STRESS_COLORS.get(stress_level, "#6b7280")
            label = STRESS_LABELS.get(stress_level, "?")
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, {color}20, {color}10);
                    border-left: 4px solid {color};
                    padding: 1rem; border-radius: 0.5rem;
                ">
                    <div style="font-weight:bold; font-size:0.9rem;">{name}</div>
                    <div style="color:{color}; font-size:1.2rem; font-weight:bold;">{label}</div>
                    <div style="font-size:0.75rem; color:#6b7280;">{line1}</div>
                    <div style="font-size:0.75rem; color:#9ca3af;">{line2}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
