"""Reusable Streamlit UI components."""

from __future__ import annotations

from typing import Any

import streamlit as st


def ffmpeg_notice() -> None:
    """Render a collapsible requirements notice."""
    with st.expander("ℹ️ Requirements", expanded=False):
        st.markdown(
            "- **ffmpeg** must be installed and on `PATH` "
            "(required for MP3 conversion and MP4 audio merging)."
        )
        st.markdown("- Only download content you have the rights to download.")


def progress_widgets() -> tuple[Any, Any]:
    """Create and return a (progress_bar, status_text) pair."""
    bar = st.progress(0.0)
    status = st.empty()
    return bar, status
