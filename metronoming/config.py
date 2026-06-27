from pathlib import Path

try:
    from kivy.app import App
    # On Android: use Kivy's user_data_dir
    _PATH = Path(App.get_running_app().user_data_dir) / "mtronoming.cfg" if App.get_running_app() else None
except (ImportError, RuntimeError):
    # Fallback for Linux CLI / non-Kivy environments
    _PATH = Path.home() / ".config" / "mtronoming.cfg"

# Ensure _PATH is valid
if _PATH is None:
    _PATH = Path.home() / ".config" / "mtronoming.cfg"

BPM_MIN = 20
BPM_MAX = 300
_DEFAULT = 120


def load_bpm() -> int:
    try:
        for line in _PATH.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "bpm":
                return max(BPM_MIN, min(BPM_MAX, int(v.strip())))
    except (FileNotFoundError, ValueError):
        pass
    return _DEFAULT


def save_bpm(bpm: int) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(f"bpm={bpm}\n")
