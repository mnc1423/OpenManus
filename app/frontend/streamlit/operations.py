"""
Async operations that interact with the OpenManus agent and planning flow.
"""

import json
from typing import List, Dict, Any

from app.agent.manus import Manus
from app.flow.flow_factory import FlowFactory, FlowType
from app.flow.planning import PlanStepStatus
from app.logger import logger


async def create_agent_and_plan(prompt: str):
    """Create the Manus agent, build a PlanningFlow, and generate the initial plan."""
    agent = await Manus.create()
    flow = FlowFactory.create_flow(
        flow_type=FlowType.PLANNING,
        agents={"manus": agent},
    )
    await flow._create_initial_plan(prompt)
    return agent, flow


def extract_react_trace(messages, start_index: int = 0) -> List[Dict[str, Any]]:
    """
    Extract the ReAct (Think → Act → Observe) trace from agent memory messages.

    Walks messages from start_index onwards and groups them into cycles:
      - Think: assistant message (LLM reasoning + tool selection)
      - Act:   tool calls embedded in the assistant message
      - Observe: tool result messages that follow

    Returns a list of cycle dicts:
      {
        "cycle": int,
        "think": str,           # LLM's reasoning text
        "tools_called": [       # tools the LLM chose
            {"name": str, "arguments": dict}
        ],
        "observations": [       # results from each tool
            {"tool": str, "result": str}
        ],
      }
    """
    trace: List[Dict[str, Any]] = []
    msgs = messages[start_index:]
    cycle_num = 0

    i = 0
    while i < len(msgs):
        msg = msgs[i]

        # A Think phase starts with an assistant message
        if msg.role == "assistant":
            cycle_num += 1
            cycle: Dict[str, Any] = {
                "cycle": cycle_num,
                "think": msg.content or "",
                "tools_called": [],
                "observations": [],
            }

            # Extract tool calls from the assistant message
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except (json.JSONDecodeError, AttributeError):
                        args = tc.function.arguments
                    cycle["tools_called"].append({
                        "name": tc.function.name,
                        "arguments": args,
                    })

            i += 1

            # Collect subsequent tool result messages (Observe phase)
            while i < len(msgs) and msgs[i].role == "tool":
                tool_msg = msgs[i]
                cycle["observations"].append({
                    "tool": tool_msg.name or "unknown",
                    "result": tool_msg.content or "",
                })
                i += 1

            trace.append(cycle)
        else:
            # Skip user/system messages (e.g. the step prompt)
            i += 1

    return trace


async def execute_step(flow, executor, step_index, step_info):
    """Execute a single plan step, capture the ReAct trace, and mark completed.

    Returns (result_text, react_trace).
    """
    plan_status = await flow._get_plan_text()
    step_text = step_info.get("text", f"Step {step_index}")

    step_prompt = f"""
    TODO LIST (from current plan):
    {plan_status}

    YOUR CURRENT TASK:
    You are now working on step {step_index}: "{step_text}"

    Please prioritize the plan: execute the next logical step, update statuses as needed, and keep the todo list in context.
    When you're done, provide a summary of what you accomplished.
    """

    # Record where agent memory starts so we can extract the trace
    mem_start = len(executor.memory.messages)

    step_result = await executor.run(step_prompt)

    # Extract the ReAct trace from new messages added during this step
    react_trace = extract_react_trace(executor.memory.messages, start_index=mem_start)

    try:
        await flow.planning_tool.execute(
            command="mark_step",
            plan_id=flow.active_plan_id,
            step_index=step_index,
            step_status=PlanStepStatus.COMPLETED.value,
        )
    except Exception as e:
        logger.warning(f"Failed to mark step {step_index} completed: {e}")

    return step_result, react_trace


async def finalize(flow):
    """Generate a final summary via the flow's LLM."""
    return await flow._finalize_plan()


async def cleanup_agent(agent):
    """Clean up agent resources."""
    try:
        await agent.cleanup()
    except Exception:
        pass
