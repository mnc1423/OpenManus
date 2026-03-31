"""
Async helpers for bridging Streamlit's synchronous runtime with async OpenManus code.
"""

import asyncio

import streamlit as st


def _get_event_loop():
    """Return (or create) a persistent event loop for running async code."""
    if "event_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        st.session_state["event_loop"] = loop
    return st.session_state["event_loop"]


def run_async(coro):
    """Run an async coroutine from synchronous Streamlit code."""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)
