"""
Reusable UI components for the Streamlit frontend.
"""

import json
from typing import List, Dict, Any

import streamlit as st

STATUS_ICONS = {
    "not_started": ":white_large_square:",
    "in_progress": ":arrow_forward:",
    "completed": ":white_check_mark:",
    "blocked": ":warning:",
}


def render_plan_table(plan_data):
    """Render the plan steps as a styled status table."""
    steps = plan_data.get("steps", [])
    statuses = plan_data.get("step_statuses", [])
    notes = plan_data.get("step_notes", [])

    for i, step in enumerate(steps):
        status = statuses[i] if i < len(statuses) else "not_started"
        note = notes[i] if i < len(notes) else ""
        icon = STATUS_ICONS.get(status, ":white_large_square:")
        label = status.replace("_", " ").title()

        cols = st.columns([0.5, 5, 2])
        with cols[0]:
            st.markdown(f"**{i}.**")
        with cols[1]:
            st.markdown(f"{icon} {step}")
            if note:
                st.caption(f"Note: {note}")
        with cols[2]:
            st.markdown(f"`{label}`")


def get_progress(plan_data):
    """Return (completed, total) counts."""
    statuses = plan_data.get("step_statuses", [])
    completed = sum(1 for s in statuses if s == "completed")
    return completed, len(statuses)


def render_progress_bar(plan_data, label_prefix="Step"):
    """Render a progress bar from plan data."""
    completed, total = get_progress(plan_data)
    if total > 0:
        st.progress(completed / total, text=f"{label_prefix} {completed}/{total} completed")
    else:
        st.progress(0.0)


def render_step_results(step_results, expanded=False):
    """Render step results with their ReAct traces as expandable sections."""
    for res in step_results:
        with st.expander(f"Step {res['index']}: {res['text']}", expanded=expanded):
            # Show the ReAct trace if available
            react_trace = res.get("react_trace", [])
            if react_trace:
                render_react_trace(react_trace)
                st.divider()

            st.markdown("**Final Result:**")
            st.markdown(res["result"])


def render_react_trace(trace: List[Dict[str, Any]]):
    """Render a ReAct Think → Act → Observe trace visually."""
    for cycle in trace:
        cycle_num = cycle["cycle"]
        st.markdown(f"##### Cycle {cycle_num}")

        # --- Think ---
        think_text = cycle.get("think", "")
        if think_text:
            st.markdown(":brain: **Think**")
            st.info(think_text)

        # --- Act ---
        tools = cycle.get("tools_called", [])
        if tools:
            st.markdown(":hammer_and_wrench: **Act**")
            for tool in tools:
                tool_name = tool["name"]
                args = tool["arguments"]
                if isinstance(args, dict):
                    args_display = json.dumps(args, indent=2, ensure_ascii=False)
                else:
                    args_display = str(args)

                st.markdown(f"Tool: `{tool_name}`")
                if args_display and args_display != "{}":
                    st.code(args_display, language="json")

        # --- Observe ---
        observations = cycle.get("observations", [])
        if observations:
            st.markdown(":mag: **Observe**")
            for obs in observations:
                tool_name = obs["tool"]
                result_text = obs["result"]
                # Truncate very long results for display
                if len(result_text) > 2000:
                    result_text = result_text[:2000] + "\n... (truncated)"
                st.markdown(f"Result from `{tool_name}`:")
                st.code(result_text, language="text")

        st.markdown("---")


# ---------------------------------------------------------------------------
# Graph colors per status
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "not_started": "#9E9E9E",   # grey
    "in_progress": "#2196F3",   # blue
    "completed": "#4CAF50",     # green
    "blocked": "#F44336",       # red
}

_STATUS_FONT_COLORS = {
    "not_started": "#FFFFFF",
    "in_progress": "#FFFFFF",
    "completed": "#FFFFFF",
    "blocked": "#FFFFFF",
}


def _escape_dot(text: str) -> str:
    """Escape special characters for Graphviz DOT labels."""
    return text.replace('"', '\\"').replace('\n', '\\n')


def _truncate(text: str, max_len: int = 40) -> str:
    """Truncate text to max_len and add ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "..."


def render_plan_graph(plan_data):
    """Render the plan steps as a top-to-bottom flow graph using st.graphviz_chart."""
    steps = plan_data.get("steps", [])
    statuses = plan_data.get("step_statuses", [])

    if not steps:
        return

    dot_lines = [
        'digraph plan {',
        '  rankdir=TB;',
        '  bgcolor="transparent";',
        '  node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=11, margin="0.3,0.15"];',
        '  edge [color="#B0BEC5", penwidth=1.5, arrowsize=0.8];',
    ]

    # Start node
    dot_lines.append(
        '  start [label="Start", shape=circle, width=0.5, '
        'fillcolor="#607D8B", fontcolor="white", fontsize=9];'
    )

    for i, step in enumerate(steps):
        status = statuses[i] if i < len(statuses) else "not_started"
        bg = _STATUS_COLORS.get(status, _STATUS_COLORS["not_started"])
        fg = _STATUS_FONT_COLORS.get(status, "#FFFFFF")
        label_status = status.replace("_", " ").upper()
        label_text = _escape_dot(_truncate(step))
        label = f"Step {i}: {label_text}\\n[{label_status}]"

        dot_lines.append(
            f'  step{i} [label="{label}", fillcolor="{bg}", fontcolor="{fg}"];'
        )

    # End node
    dot_lines.append(
        '  end [label="Done", shape=doublecircle, width=0.5, '
        'fillcolor="#607D8B", fontcolor="white", fontsize=9];'
    )

    # Edges: start -> step0 -> step1 -> ... -> end
    dot_lines.append(f'  start -> step0;')
    for i in range(len(steps) - 1):
        dot_lines.append(f'  step{i} -> step{i + 1};')
    dot_lines.append(f'  step{len(steps) - 1} -> end;')

    dot_lines.append('}')

    dot_source = '\n'.join(dot_lines)
    st.graphviz_chart(dot_source, use_container_width=True)
