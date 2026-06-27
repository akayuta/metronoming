import sys

# Try Kivy first, fallback to CLI
try:
    from .main import main
except ImportError:
    from .tui import run as main


if __name__ == "__main__":
    main()
