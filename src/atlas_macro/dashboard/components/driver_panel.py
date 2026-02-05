"""
ATLAS MACRO - Driver Panel Component

Displays the active stress drivers list.
"""

import streamlit as st


def render_driver_panel(drivers: list[str]) -> None:
    """Render the active drivers list."""
    st.markdown("### Active Drivers")

    if not drivers or drivers == ["All metrics within normal ranges"]:
        st.success("No active stress drivers. All metrics within normal ranges.")
        return

    for driver in drivers:
        st.markdown(f"- {driver}")
