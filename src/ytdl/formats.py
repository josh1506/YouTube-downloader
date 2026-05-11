"""Format and quality detection for YouTube videos via yt-dlp."""

from __future__ import annotations

import streamlit as st
import yt_dlp

from ytdl.exceptions import (
    InvalidLanguageError,
    InvalidQualityError,
    NoFormatsFoundError,
)


@st.cache_data(show_spinner=False)
def fetch_info(url: str) -> dict:
    """Fetch video metadata from YouTube without downloading.

    Results are cached per URL for the duration of the Streamlit session.
    """
    opts: dict = {"quiet": True, "skip_download": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def available_mp4_qualities(info: dict) -> list[int]:
    """Return all MP4 heights available for *info*, sorted highest first."""
    quality_set: set[int] = set()
    for fmt in info.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        if fmt.get("ext") != "mp4" or fmt.get("vcodec") in (None, "none"):
            continue
        height = fmt.get("height")
        if isinstance(height, int):
            quality_set.add(height)

    if not quality_set:
        raise NoFormatsFoundError("No MP4 streams were found for this video.")

    return sorted(quality_set, reverse=True)


def available_audio_languages(info: dict) -> list[str]:
    """Return audio language codes available in the format list."""
    langs: set[str] = set()
    for fmt in info.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        if fmt.get("acodec") in (None, "none"):
            continue
        language = fmt.get("language")
        if isinstance(language, str) and language.strip():
            langs.add(language.strip())
    return sorted(langs)


def _validate_audio_language(info: dict, audio_language: str | None) -> None:
    if audio_language is None:
        return

    langs = available_audio_languages(info)
    if langs and audio_language not in langs:
        raise InvalidLanguageError(
            f"Audio language '{audio_language}' is not available for this video."
        )


def build_audio_selector(*, info: dict, audio_language: str | None) -> str:
    """Build a yt-dlp selector string for audio-only downloads."""
    _validate_audio_language(info, audio_language)
    if audio_language is None:
        return "bestaudio/best"
    return f"bestaudio[language={audio_language}]/bestaudio/best"


def _best_video_only_format(info: dict, quality: int) -> str:
    """Return the format_id for the best-bitrate video-only MP4 at *quality*."""
    matches = [
        fmt
        for fmt in (info.get("formats") or [])
        if isinstance(fmt, dict)
        and fmt.get("ext") == "mp4"
        and fmt.get("vcodec") not in (None, "none")
        and fmt.get("acodec") == "none"
        and fmt.get("height") == quality
    ]
    if not matches:
        raise InvalidQualityError(
            f"No video-only MP4 stream is available at {quality}p."
        )
    return str(max(matches, key=lambda f: f.get("tbr") or 0)["format_id"])


def build_format_selector(
    quality: int,
    *,
    with_audio: bool,
    info: dict,
    audio_language: str | None = None,
) -> str:
    """Build a yt-dlp format selector string for the requested quality."""
    if with_audio:
        _validate_audio_language(info, audio_language)
        lang_filter = f"[language={audio_language}]" if audio_language else ""
        return (
            f"bestvideo[ext=mp4][height={quality}]"
            f"+bestaudio[ext=m4a]{lang_filter}/"
            f"bestvideo[height={quality}]+bestaudio{lang_filter}/"
            f"bestvideo[height={quality}]+bestaudio/best[height={quality}]"
        )
    return _best_video_only_format(info, quality)
