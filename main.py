"""Entry point — run with: streamlit run main.py"""

from pathlib import Path
import sys
from importlib import import_module

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
main = import_module("ytdl.ui.app").main

if __name__ == "__main__":
    main()
