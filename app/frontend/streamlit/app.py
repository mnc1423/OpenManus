"""
Streamlit frontend for OpenManus - Planning Flow with interactive TODO list.

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

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="OpenManus", page_icon=":robot_face:", layout="wide")
st.title(":robot_face: OpenManus")
st.caption("AI Agent with Planning Flow")

# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------

init_state()

# ---------------------------------------------------------------------------
# Route to the active phase
# ---------------------------------------------------------------------------

PHASE_RENDERERS = {
    "input": input_phase.render,
    "review": review_phase.render,
    "executing": executing_phase.render,
    "done": done_phase.render,
}

phase = st.session_state["phase"]
renderer = PHASE_RENDERERS.get(phase)
if renderer:
    renderer()
else:
    st.error(f"Unknown phase: {phase}")
