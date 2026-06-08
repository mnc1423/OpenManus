"""
Streamlit frontend for OpenManus - Planning Flow with interactive TODO list + Team Management.

This is the main entry point. It sets up the page and routes to the
appropriate phase renderer based on session state.
"""

import sys
from pathlib import Path

import streamlit as st

# Ensure the project root is on sys.path so `app.*` imports resolve
PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.frontend.streamlit.state import init_state
from app.frontend.streamlit.pages import (
    input_phase,
    review_phase,
    executing_phase,
    done_phase,
)
from app.frontend.streamlit import team_ui
from app.team import TeamManager
from app.logger import logger

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Multi Agent Canvas", page_icon=":robot_face:", layout="wide"
)
st.title(":robot_face: Multi Agent Canvas")
st.caption("AI Agent with Planning Flow + Team Collaboration")

# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------

init_state()

# Initialize TeamManager if not already in session
if st.session_state.get("team_manager") is None:
    st.session_state["team_manager"] = TeamManager()

team_manager = st.session_state["team_manager"]

# ---------------------------------------------------------------------------
# Sidebar: Tab Navigation (Execution vs Teams)
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
tab1, tab2 = st.sidebar.tabs(["🚀 Execution", "👥 Teams"])

with tab1:
    st.markdown("**Agent Execution**")
    # Existing execution sidebar content can go here

with tab2:
    st.markdown("**Team Management**")

    # Render team sidebar
    selected_team_id = team_ui.render_team_sidebar(team_manager)

    if selected_team_id:
        st.session_state["selected_team_id"] = selected_team_id
        st.session_state["selected_team"] = team_manager.get_team(selected_team_id)

# Handle modals
if st.session_state.get("show_create_team_modal", False):
    # Get available agents (can be customized based on your agent registry)
    available_agents = []  # TODO: Get from agent registry when implemented
    team_ui.render_create_team_modal(team_manager, available_agents)

if st.session_state.get("show_team_settings", False):
    selected_team = st.session_state.get("selected_team")
    if selected_team:
        available_agents = []  # TODO: Get from agent registry
        team_ui.render_team_settings_modal(
            team_manager, selected_team, available_agents
        )

if st.session_state.get("show_dissolve_confirm", False):
    selected_team = st.session_state.get("selected_team")
    if selected_team:
        team_ui.render_dissolve_confirm(team_manager, selected_team)

# ---------------------------------------------------------------------------
# Route to the active phase
# ---------------------------------------------------------------------------

phase = st.session_state["phase"]

# Check if a team is selected - if so, show team chat
if st.session_state.get("selected_team_id") and phase not in ["review", "executing"]:
    st.session_state["phase"] = "team_chat"
    phase = "team_chat"

if phase == "team_chat":
    selected_team = st.session_state.get("selected_team")
    if selected_team:
        team_ui.render_team_chat(selected_team)
    else:
        st.info("Select a team from the sidebar to start collaborating")
else:
    PHASE_RENDERERS = {
        "input": input_phase.render,
        "review": review_phase.render,
        "executing": executing_phase.render,
        "done": done_phase.render,
    }

    renderer = PHASE_RENDERERS.get(phase)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown phase: {phase}")
