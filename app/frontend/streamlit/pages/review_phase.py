"""
Phase: REVIEW - User reviews and edits the TODO list before execution.
"""

import streamlit as st

from app.frontend.streamlit.async_utils import run_async
from app.frontend.streamlit.operations import cleanup_agent
from app.frontend.streamlit.state import reset_state


def render():
    flow = st.session_state["flow"]
    plan_data = st.session_state["plan_data"]

    st.markdown("### :clipboard: Review & Edit TODO List")
    st.info(f"**Prompt:** {st.session_state['prompt']}")

    st.markdown(f"**{plan_data.get('title', 'Untitled Plan')}**")
    st.divider()

    steps = plan_data.get("steps", [])

    # Editable steps
    edited_steps = []
    steps_to_remove = []

    for i, step in enumerate(steps):
        cols = st.columns([0.5, 5, 1])
        with cols[0]:
            st.markdown(f"**{i}.**")
        with cols[1]:
            edited = st.text_input(
                f"Step {i}",
                value=step,
                key=f"step_edit_{i}",
                label_visibility="collapsed",
            )
            edited_steps.append(edited)
        with cols[2]:
            if st.button(":x:", key=f"remove_{i}", help="Remove this step"):
                steps_to_remove.append(i)

    # Apply removals
    if steps_to_remove:
        new_steps = [s for idx, s in enumerate(edited_steps) if idx not in steps_to_remove]
        run_async(flow.planning_tool.execute(
            command="update",
            plan_id=flow.active_plan_id,
            steps=new_steps,
        ))
        st.session_state["plan_data"] = flow.planning_tool.plans[flow.active_plan_id]
        st.rerun()

    # Add step
    st.divider()
    add_cols = st.columns([5, 1])
    with add_cols[0]:
        new_step = st.text_input(
            "New step",
            key="new_step_input",
            placeholder="Enter a new step...",
            label_visibility="collapsed",
        )
    with add_cols[1]:
        if st.button(":heavy_plus_sign: Add", disabled=not new_step.strip()):
            updated_steps = edited_steps + [new_step.strip()]
            run_async(flow.planning_tool.execute(
                command="update",
                plan_id=flow.active_plan_id,
                steps=updated_steps,
            ))
            st.session_state["plan_data"] = flow.planning_tool.plans[flow.active_plan_id]
            st.rerun()

    # Save inline edits (if any text was changed but no add/remove)
    if edited_steps != steps:
        run_async(flow.planning_tool.execute(
            command="update",
            plan_id=flow.active_plan_id,
            steps=edited_steps,
        ))
        st.session_state["plan_data"] = flow.planning_tool.plans[flow.active_plan_id]

    # Navigation buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button(":arrow_left: Back", use_container_width=True):
            run_async(cleanup_agent(st.session_state["agent"]))
            reset_state()
            st.rerun()
    with col2:
        if st.button(":arrow_forward: Execute Plan", type="primary", use_container_width=True):
            st.session_state["phase"] = "executing"
            st.rerun()
