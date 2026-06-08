"""
Phase: INPUT - User enters their task prompt and generates a plan.
"""

import streamlit as st

from app.agent.manus import TOGGLEABLE_TOOLS
from app.frontend.streamlit.async_utils import run_async
from app.frontend.streamlit.operations import create_agent_and_plan


def _render_tool_selector() -> list:
    """Render the per-session tool toggles and return the list of enabled names."""
    with st.expander("🛠️ Tools", expanded=False):
        st.caption(
            "Enable or disable the tools the agent may use for this run. "
            "`terminate` is always available."
        )
        enabled = []
        for name, (_factory, label, description, default) in TOGGLEABLE_TOOLS.items():
            checked = st.checkbox(
                label,
                value=default,
                key=f"tool_toggle_{name}",
                help=description,
            )
            if checked:
                enabled.append(name)
        if not enabled:
            st.warning("No tools selected — the agent will only be able to terminate.")
    return enabled


def render():
    st.markdown("### What would you like to accomplish?")
    prompt = st.text_area(
        "Enter your task prompt",
        height=120,
        placeholder="e.g. Build a Python web scraper that collects news headlines...",
    )

    enabled_tools = _render_tool_selector()

    if st.button(":rocket: Generate Plan", type="primary", disabled=not prompt.strip()):
        with st.spinner("Creating agent and generating plan..."):
            try:
                st.session_state["enabled_tools"] = enabled_tools
                agent, flow = run_async(
                    create_agent_and_plan(prompt.strip(), enabled_tools)
                )
                plan_data = flow.planning_tool.plans.get(flow.active_plan_id)
                if not plan_data:
                    st.error("Plan creation failed. Please try again.")
                    st.stop()

                st.session_state["prompt"] = prompt.strip()
                st.session_state["agent"] = agent
                st.session_state["flow"] = flow
                st.session_state["plan_data"] = plan_data
                st.session_state["phase"] = "review"
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
