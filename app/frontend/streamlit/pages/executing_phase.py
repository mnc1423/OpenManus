"""
Phase: EXECUTING - Steps are executed one by one with live status updates.
"""

import streamlit as st

from app.flow.planning import PlanStepStatus
from app.logger import logger

from app.frontend.streamlit.async_utils import run_async
from app.frontend.streamlit.operations import execute_step, finalize
from app.frontend.streamlit.ui_components import (
    render_plan_graph,
    render_plan_table,
    render_progress_bar,
    render_step_results,
)


def render():
    flow = st.session_state["flow"]
    plan_data = flow.planning_tool.plans.get(flow.active_plan_id, {})

    st.markdown("### :gear: Execution in Progress")
    st.info(f"**Prompt:** {st.session_state['prompt']}")

    # Progress
    render_progress_bar(plan_data, label_prefix="Step")

    # Show plan as flow graph
    render_plan_graph(plan_data)

    # Show plan status table
    with st.expander("Step details", expanded=False):
        render_plan_table(plan_data)

    st.divider()

    # Show previous results
    render_step_results(st.session_state["step_results"])

    # Find next step to execute
    steps = plan_data.get("steps", [])
    statuses = plan_data.get("step_statuses", [])

    next_index = None
    for i, status in enumerate(statuses):
        if status in PlanStepStatus.get_active_statuses():
            next_index = i
            break

    if next_index is not None:
        step_text = steps[next_index]

        # Mark as in-progress
        try:
            run_async(flow.planning_tool.execute(
                command="mark_step",
                plan_id=flow.active_plan_id,
                step_index=next_index,
                step_status=PlanStepStatus.IN_PROGRESS.value,
            ))
        except Exception:
            pass

        st.markdown(f"#### :arrow_forward: Running Step {next_index}: *{step_text}*")

        with st.spinner(f"Executing step {next_index}..."):
            try:
                step_info = {"text": step_text}
                executor = flow.get_executor()
                result, react_trace = run_async(
                    execute_step(flow, executor, next_index, step_info)
                )

                st.session_state["step_results"].append({
                    "index": next_index,
                    "text": step_text,
                    "result": result,
                    "react_trace": react_trace,
                })
                st.session_state["plan_data"] = flow.planning_tool.plans.get(
                    flow.active_plan_id, {}
                )
                st.rerun()

            except Exception as e:
                st.error(f"Error executing step {next_index}: {e}")
                logger.error(f"Step execution error: {e}")
                # Mark blocked
                try:
                    run_async(flow.planning_tool.execute(
                        command="mark_step",
                        plan_id=flow.active_plan_id,
                        step_index=next_index,
                        step_status=PlanStepStatus.BLOCKED.value,
                        step_notes=str(e),
                    ))
                except Exception:
                    pass
                st.session_state["plan_data"] = flow.planning_tool.plans.get(
                    flow.active_plan_id, {}
                )
                st.session_state["phase"] = "done"
                st.session_state["error"] = str(e)
                st.rerun()
    else:
        # All steps done - finalize
        with st.spinner("Generating summary..."):
            try:
                summary = run_async(finalize(flow))
            except Exception:
                summary = "Plan execution completed."
        st.session_state["summary"] = summary
        st.session_state["phase"] = "done"
        st.session_state["plan_data"] = flow.planning_tool.plans.get(
            flow.active_plan_id, {}
        )
        st.rerun()
