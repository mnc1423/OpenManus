"""
Session state management and defaults for the Streamlit app.
"""

import streamlit as st

DEFAULTS = {
    "phase": "input",  # input | review | executing | done | team_chat
    "prompt": "",
    "agent": None,
    "flow": None,
    "plan_data": None,
    "step_results": [],
    "current_step": None,
    "error": None,
    # Team-related state
    "team_manager": None,
    "selected_team_id": None,
    "selected_team": None,
    "show_create_team_modal": False,
    "show_team_settings": False,
    "show_dissolve_confirm": False,
    "settings_team_id": None,
    "team_rules_count": 1,
    "edit_team_rules_count": 1,
}


def init_state():
    """Initialize session state with defaults for any missing keys."""
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_state():
    """Reset all session state to defaults."""
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    if "summary" in st.session_state:
        del st.session_state["summary"]
