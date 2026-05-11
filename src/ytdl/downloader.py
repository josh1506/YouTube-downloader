"""Core download logic with real-time progress reporting."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import yt_dlp

from ytdl.config import DEFAULT_OUTPUT_DIR, MP3_BITRATE
from ytdl.exceptions import InvalidQualityError
from ytdl.formats import build_audio_selector, build_format_selector

ProgressCallback = Callable[[float, str], None]


def _make_progress_hook(on_progress: ProgressCallback | None) -> Callable[[dict], None]:
    """Return a yt-dlp progress hook that forwards real download stats."""

    def _hook(d: dict) -> None:
        if on_progress is None:
            return

        status = d.get("status")

        if status == "downloading":
            total: int | None = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded: int = d.get("downloaded_bytes") or 0
            speed: float | None = d.get("speed")
            eta: int | None = d.get("eta")

            pct = (downloaded / total) if total else 0.0
            speed_str = f"{speed / 1_048_576:.1f} MB/s" if speed else "..."
            eta_str = f"{eta}s" if eta is not None else "..."
            on_progress(
                min(pct, 1.0),
                f"{pct * 100:.1f}%  —  {speed_str}  —  ETA {eta_str}",
            )

        elif status == "finished":
            on_progress(1.0, "Processing…")

    return _hook


def _build_ydl_opts(
    *,
    mode: str,
    quality: int | None,
    with_audio: bool,
    audio_language: str | None,
    output_template: str,
    info: dict,
    on_progress: ProgressCallback | None,
) -> dict:
    base: dict = {
        "outtmpl": output_template,
        "noplaylist": True,
        "progress_hooks": [_make_progress_hook(on_progress)],
    }

    if mode == "mp3":
        return {
            **base,
            "format": build_audio_selector(info=info, audio_language=audio_language),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": MP3_BITRATE,
                }
            ],
        }

    if quality is None:
        raise InvalidQualityError("A quality must be selected for MP4 downloads.")

    return {
        **base,
        "format": build_format_selector(
            quality,
            with_audio=with_audio,
            info=info,
            audio_language=audio_language,
        ),
        "merge_output_format": "mp4",
    }


def download(
    *,
    url: str,
    info: dict,
    mode: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    quality: int | None = None,
    with_audio: bool = True,
    audio_language: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[Path]:
    """Download *url* and return the list of output files created."""
    title = str(info.get("title") or "video")
    safe_title = (
        "".join(ch for ch in title if ch not in r'<>:"/\|?*').strip() or "video"
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / f"{safe_title}.%(ext)s")

    ydl_opts = _build_ydl_opts(
        mode=mode,
        quality=quality,
        with_audio=with_audio,
        audio_language=audio_language,
        output_template=output_template,
        info=info,
        on_progress=on_progress,
    )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        before = {p for p in out_dir.iterdir() if p.is_file()}
        ydl.download([url])
        after = {p for p in out_dir.iterdir() if p.is_file()}

    new_files = sorted(after - before, key=lambda p: p.stat().st_mtime, reverse=True)
    if new_files:
        return new_files

    # Fallback: locate by name pattern if snapshot diff missed the file.
    suffix = ".mp3" if mode == "mp3" else ".mp4"
    return sorted(
        out_dir.glob(f"{safe_title}*{suffix}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
