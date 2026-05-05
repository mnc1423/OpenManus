"""
Streamlit UI components for team management.

Provides sidebar UI and modals for creating, managing, and interacting with teams.
"""

import streamlit as st
from typing import List, Optional
from app.team import Team, TeamManager
from app.logger import logger


def render_team_sidebar(team_manager: TeamManager) -> Optional[str]:
    """Render team list in sidebar.

    Returns:
        Selected team ID, or None if no team selected.
    """
    st.sidebar.markdown("### 👥 Teams")

    col1, col2 = st.sidebar.columns([1, 0.4])
    with col1:
        st.markdown("**Your Teams**")
    with col2:
        if st.button("➕ Create", key="create_team_btn", use_container_width=True):
            st.session_state["show_create_team_modal"] = True

    teams = team_manager.get_all_teams()

    if not teams:
        st.sidebar.info("No teams yet. Create one to get started!")
        return None

    selected_team_id = None
    for team in teams:
        col1, col2 = st.sidebar.columns([0.85, 0.15])
        with col1:
            if st.button(
                f"**{team.name}**\n{len(team.agent_ids)} members",
                key=f"team_{team.id}",
                use_container_width=True,
            ):
                selected_team_id = team.id
                st.session_state["selected_team_id"] = team.id

        with col2:
            if st.button("⚙️", key=f"settings_{team.id}", use_container_width=True):
                st.session_state["show_team_settings"] = True
                st.session_state["settings_team_id"] = team.id

    # Highlight selected team
    if "selected_team_id" in st.session_state:
        return st.session_state["selected_team_id"]

    return None


def render_create_team_modal(team_manager: TeamManager, available_agents: List) -> bool:
    """Render modal for creating a new team.

    Returns:
        True if team was created, False otherwise.
    """
    if not st.session_state.get("show_create_team_modal", False):
        return False

    # Modal overlay
    col_left, col_modal, col_right = st.columns([0.05, 0.9, 0.05])
    with col_modal:
        modal = st.container(border=True)
        with modal:
            col_close = st.columns([0.95, 0.05])
            with col_close[1]:
                if st.button("✕", key="close_create_modal", help="Close"):
                    st.session_state["show_create_team_modal"] = False
                    st.rerun()

            st.markdown("#### Create New Team")
            st.markdown("---")

            # Team name
            team_name = st.text_input(
                "Team Name",
                placeholder="e.g., Marketing Team",
                key="new_team_name",
            )

            # Team goal
            team_goal = st.text_area(
                "Core Goal",
                placeholder="What is this team's main objective?",
                height=80,
                key="new_team_goal",
            )

            # Team rules
            st.markdown("**Team Rules** (optional)")
            rules = []

            # Add initial empty rule slot
            if "team_rules_count" not in st.session_state:
                st.session_state["team_rules_count"] = 1

            for i in range(st.session_state["team_rules_count"]):
                rule_text = st.text_input(
                    f"Rule {i + 1}",
                    placeholder=f"e.g., Always use data to support decisions",
                    key=f"team_rule_{i}",
                )
                if rule_text.strip():
                    rules.append(rule_text.strip())

            if st.button("+ Add Rule", key="add_rule_btn", use_container_width=False):
                st.session_state["team_rules_count"] += 1
                st.rerun()

            # Member selection
            st.markdown("**Select Members**")
            selected_agent_ids = []
            for agent in available_agents:
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    if st.checkbox(
                        "",
                        key=f"agent_{agent.name if hasattr(agent, 'name') else agent}",
                    ):
                        selected_agent_ids.append(
                            agent.name if hasattr(agent, "name") else str(agent)
                        )
                with col2:
                    agent_name = agent.name if hasattr(agent, "name") else str(agent)
                    agent_desc = (
                        agent.description if hasattr(agent, "description") else ""
                    )
                    st.write(
                        f"**{agent_name}**\n{agent_desc if agent_desc else 'No description'}"
                    )

            st.markdown("---")
            # Create button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Team", type="primary", use_container_width=True):
                    if not team_name.strip():
                        st.error("Team name is required")
                        return False

                    try:
                        from app.frontend.streamlit.utils import generate_id

                        team_id = generate_id()
                        team_manager.create_team(
                            team_id=team_id,
                            name=team_name.strip(),
                            goal=team_goal.strip(),
                            rules=rules,
                        )

                        # Add agents to team
                        for agent_id in selected_agent_ids:
                            team_manager.add_agent_to_team(team_id, agent_id)

                        st.success(f"✅ Team '{team_name}' created!")
                        st.session_state["show_create_team_modal"] = False
                        st.session_state["team_rules_count"] = 1
                        st.rerun()
                        return True

                    except Exception as e:
                        st.error(f"Failed to create team: {e}")
                        logger.error(f"Team creation error: {e}")
                        return False

            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["show_create_team_modal"] = False
                    st.rerun()

    return False


def render_team_settings_modal(
    team_manager: TeamManager, team: Team, available_agents: List
) -> bool:
    """Render modal for editing team settings.

    Returns:
        True if team was updated, False otherwise.
    """
    if not st.session_state.get("show_team_settings", False):
        return False

    with st.dialog(f"Team Settings: {team.name}", width="large"):
        st.markdown("#### Modify Team")

        # Goal
        goal = st.text_area(
            "Core Goal",
            value=team.goal,
            height=80,
            key="edit_team_goal",
        )

        # Rules
        st.markdown("**Team Rules**")
        rules = []
        if "edit_team_rules_count" not in st.session_state:
            st.session_state["edit_team_rules_count"] = len(team.rules) or 1

        for i in range(st.session_state["edit_team_rules_count"]):
            rule_text = st.text_input(
                f"Rule {i + 1}",
                value=team.rules[i] if i < len(team.rules) else "",
                key=f"edit_team_rule_{i}",
            )
            if rule_text.strip():
                rules.append(rule_text.strip())

        if st.button("+ Add Rule", key="add_edit_rule_btn", use_container_width=False):
            st.session_state["edit_team_rules_count"] += 1
            st.rerun()

        # Members
        st.markdown("**Team Members**")
        selected_agent_ids = []
        for agent in available_agents:
            agent_id = agent.name if hasattr(agent, "name") else str(agent)
            is_member = agent_id in team.agent_ids
            agent_name = agent.name if hasattr(agent, "name") else str(agent)
            agent_desc = agent.description if hasattr(agent, "description") else ""

            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.checkbox("", value=is_member, key=f"edit_agent_{agent_id}"):
                    selected_agent_ids.append(agent_id)
            with col2:
                st.write(
                    f"**{agent_name}**\n{agent_desc if agent_desc else 'No description'}"
                )

        # Buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Save Changes", type="primary", use_container_width=True):
                try:
                    team_manager.update_team_goal(team.id, goal.strip())
                    team_manager.update_team_rules(team.id, rules)
                    team_manager.set_team_agents(team.id, selected_agent_ids)

                    st.success("✅ Team updated!")
                    st.session_state["show_team_settings"] = False
                    st.rerun()
                    return True

                except Exception as e:
                    st.error(f"Failed to update team: {e}")
                    logger.error(f"Team update error: {e}")
                    return False

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_team_settings"] = False
                st.rerun()

        with col3:
            if st.button("🗑️ Dissolve Team", type="secondary", use_container_width=True):
                st.session_state["show_dissolve_confirm"] = True
                st.rerun()

    return False


def render_dissolve_confirm(team_manager: TeamManager, team: Team) -> bool:
    """Render confirmation dialog for dissolving a team.

    Returns:
        True if team was dissolved, False otherwise.
    """
    if not st.session_state.get("show_dissolve_confirm", False):
        return False

    with st.dialog("Dissolve Team?", width="small"):
        st.warning(
            f"Are you sure you want to dissolve **{team.name}**? "
            "All team chat history will be deleted, but agents will remain.",
            icon="⚠️",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Dissolve", type="primary", use_container_width=True):
                try:
                    team_manager.dissolve_team(team.id)
                    st.success(f"✅ Team '{team.name}' dissolved")
                    st.session_state["show_team_settings"] = False
                    st.session_state["show_dissolve_confirm"] = False
                    st.session_state["selected_team_id"] = None
                    st.rerun()
                    return True
                except Exception as e:
                    st.error(f"Failed to dissolve team: {e}")
                    logger.error(f"Team dissolve error: {e}")
                    return False

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_dissolve_confirm"] = False
                st.rerun()

    return False


def render_team_chat(team: Team) -> None:
    """Render team chat interface.

    Shows team messages and provides input for sending messages.
    """
    st.markdown(f"### 👥 {team.name}")
    st.markdown(f"**Goal:** {team.goal or '(Not set)'}")

    if team.rules:
        with st.expander("📋 Team Rules"):
            for i, rule in enumerate(team.rules, 1):
                st.write(f"{i}. {rule}")

    # Chat history
    st.markdown("#### Messages")
    if not team.messages:
        st.info("No messages yet. Start the conversation!")
    else:
        for msg in team.messages:
            if msg.role == "user":
                with st.chat_message("user"):
                    st.write(f"**You** → {msg.mention_target}")
                    st.write(msg.content)
                    st.caption(msg.timestamp.strftime("%H:%M"))
            else:
                with st.chat_message("assistant"):
                    st.write(f"**{msg.sender_name}**")
                    st.write(msg.content)
                    st.caption(msg.timestamp.strftime("%H:%M"))

    # Input area
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        mention_target = st.selectbox(
            "To",
            options=["@all"] + [f"@{agent_id}" for agent_id in team.agent_ids],
            key="team_mention",
        )

    with col2:
        user_input = st.text_input(
            "Type a message...",
            placeholder="Ask your team something...",
            key="team_message_input",
        )

    with col3:
        send_btn = st.button("Send", type="primary", use_container_width=True)

    if send_btn and user_input.strip():
        from app.frontend.streamlit.utils import generate_id

        msg_id = generate_id()
        team_manager = st.session_state.get("team_manager")
        if team_manager:
            team_manager.add_message_to_team(
                team.id, msg_id, "user", user_input.strip(), "You", mention_target
            )
            st.session_state["team_message_input"] = ""
            st.rerun()
