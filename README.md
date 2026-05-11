# YouTube Downloader (Streamlit)

This app accepts a YouTube link and lets you download as:

- MP4 with audio
- MP4 without audio
- MP3

For MP4, it shows only qualities that are actually available for that video (such as 8k, 4k, 1080p, 720p, 480p, 360p).

## Requirements

- Python 3.13+
- ffmpeg installed and added to PATH (needed for MP3 conversion and MP4 audio merging)

## Install dependencies

```bash
pip install -e .
```

or:

```bash
pip install streamlit yt-dlp
```

## Run app

```bash
streamlit run main.py
```

## How to use

1. Paste a YouTube URL.
2. Choose `MP4` or `MP3`.
3. If MP4:
	- select whether to include audio
	- pick `best` or a specific available quality
4. Click **Download**.
5. Files are saved to the output folder (default: `downloads`).

## Note

Download only content you have rights to download and use.
