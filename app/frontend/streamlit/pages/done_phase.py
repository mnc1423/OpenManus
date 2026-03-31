"""
Phase: DONE - Execution complete, show results and summary.
"""

import streamlit as st

from app.frontend.streamlit.async_utils import run_async
from app.frontend.streamlit.operations import cleanup_agent
from app.frontend.streamlit.state import reset_state
from app.frontend.streamlit.ui_components import (
    render_plan_graph,
    render_plan_table,
    render_progress_bar,
    render_step_results,
)


def render():
    flow = st.session_state["flow"]
    plan_data = flow.planning_tool.plans.get(flow.active_plan_id, {}) if flow else {}

    st.markdown("### :checkered_flag: Execution Complete")

    if st.session_state.get("error"):
        st.error(f"Execution stopped due to error: {st.session_state['error']}")

    # Final plan status
    render_progress_bar(plan_data)

    # Flow graph
    render_plan_graph(plan_data)

    st.markdown("#### Final Plan Status")
    with st.expander("Step details", expanded=False):
        render_plan_table(plan_data)

    # Step results
    st.divider()
    st.markdown("#### Step Results")
    render_step_results(st.session_state["step_results"])

    # Summary
    if st.session_state.get("summary"):
        st.divider()
        st.markdown("#### Summary")
        st.markdown(st.session_state["summary"])

    # Cleanup and restart
    st.divider()
    if st.button(":arrows_counterclockwise: Start New Task", type="primary"):
        if st.session_state.get("agent"):
            run_async(cleanup_agent(st.session_state["agent"]))
        reset_state()
        st.rerun()
