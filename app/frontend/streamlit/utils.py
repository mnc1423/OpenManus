"""
Utility functions for Streamlit frontend.
"""

import uuid
import random
import string


def generate_id() -> str:
    """Generate a unique ID.

    Returns:
        A unique string ID combining timestamp-based UUID and random suffix.
    """
    return f"{uuid.uuid4().hex[:8]}{random.randint(1000, 9999)}"


def format_timestamp(timestamp) -> str:
    """Format a datetime object for display."""
    if timestamp is None:
        return ""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
