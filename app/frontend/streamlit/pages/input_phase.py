"""
Phase: INPUT - User enters their task prompt and generates a plan.
"""

import streamlit as st

from app.frontend.streamlit.async_utils import run_async
from app.frontend.streamlit.operations import create_agent_and_plan


def render():
    st.markdown("### What would you like to accomplish?")
    prompt = st.text_area(
        "Enter your task prompt",
        height=120,
        placeholder="e.g. Build a Python web scraper that collects news headlines...",
    )

    if st.button(":rocket: Generate Plan", type="primary", disabled=not prompt.strip()):
        with st.spinner("Creating agent and generating plan..."):
            try:
                agent, flow = run_async(create_agent_and_plan(prompt.strip()))
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
