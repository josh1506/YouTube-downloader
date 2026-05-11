"""Streamlit application layout and event handling."""

from __future__ import annotations

import yt_dlp
import streamlit as st

from ytdl.config import APP_ICON, APP_TITLE, DEFAULT_OUTPUT_DIR
from ytdl.downloader import download
from ytdl.exceptions import (
    InvalidLanguageError,
    InvalidQualityError,
    NoFormatsFoundError,
    YTDLError,
)
from ytdl.formats import available_audio_languages, available_mp4_qualities, fetch_info
from ytdl.ui.components import ffmpeg_notice, progress_widgets


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("Download YouTube videos as MP4 (with or without audio) or MP3.")

    ffmpeg_notice()

    # ── Inputs ────────────────────────────────────────────────────────────────
    url = st.text_input(
        "YouTube URL", placeholder="https://www.youtube.com/watch?v=..."
    )
    output_dir = st.text_input("Output folder", value=DEFAULT_OUTPUT_DIR)
    mode: str = st.radio("Download as", ["MP4", "MP3"], horizontal=True)  # type: ignore[assignment]

    with_audio = True
    selected_quality: int | None = None
    selected_audio_language: str | None = None

    if not url:
        st.info("Paste a YouTube URL above to get started.")
        return

    # ── Video metadata ────────────────────────────────────────────────────────
    try:
        with st.spinner("Loading video info…"):
            info = fetch_info(url)
    except Exception as exc:
        st.error(f"Could not load this URL: {exc}")
        return

    st.subheader(str(info.get("title") or "Unknown title"))
    audio_languages = available_audio_languages(info)

    if mode == "MP3":
        if audio_languages:
            selected = st.selectbox(
                "Audio language", options=["auto"] + audio_languages
            )
            selected_audio_language = None if selected == "auto" else selected
            st.caption("Detected audio tracks: " + ", ".join(audio_languages))
        else:
            st.caption(
                "No audio language metadata found; default track selection will be used."
            )

    # ── MP4-specific options ──────────────────────────────────────────────────
    if mode == "MP4":
        try:
            qualities = available_mp4_qualities(info)
        except NoFormatsFoundError as exc:
            st.error(str(exc))
            return

        with_audio = st.toggle("Include audio", value=True)
        if with_audio:
            if audio_languages:
                selected = st.selectbox(
                    "Audio language",
                    options=["auto"] + audio_languages,
                    key="mp4_audio_language",
                )
                selected_audio_language = None if selected == "auto" else selected
                st.caption("Detected audio tracks: " + ", ".join(audio_languages))
            else:
                st.caption(
                    "No audio language metadata found; default track selection will be used."
                )

        quality_options = ["best"] + [f"{q}p" for q in qualities]
        selected = st.selectbox("Quality", options=quality_options)
        selected_quality = qualities[0] if selected == "best" else int(selected[:-1])  # type: ignore[index]
        st.caption("Available: " + ", ".join(f"{q}p" for q in qualities))

    # ── Download ──────────────────────────────────────────────────────────────
    if not st.button("⬇ Download", type="primary"):
        return

    bar, status = progress_widgets()

    def on_progress(pct: float, label: str) -> None:
        bar.progress(pct)
        status.text(label)

    try:
        files = download(
            url=url,
            info=info,
            mode=mode.lower(),
            output_dir=output_dir,
            quality=selected_quality,
            with_audio=with_audio,
            audio_language=selected_audio_language,
            on_progress=on_progress,
        )
        bar.progress(1.0)
        status.empty()

        if not files:
            st.warning("Download finished, but the output file could not be located.")
            return

        st.success("✅ Download completed.")
        for f in files[:3]:
            st.code(str(f))

    except yt_dlp.utils.DownloadError as exc:
        bar.empty()
        status.empty()
        st.error(str(exc))
        st.info("Ensure **ffmpeg** is installed and on PATH.")
    except (YTDLError, InvalidQualityError, InvalidLanguageError) as exc:
        bar.empty()
        status.empty()
        st.error(str(exc))
    except Exception as exc:
        bar.empty()
        status.empty()
        st.error(f"Unexpected error: {exc}")
