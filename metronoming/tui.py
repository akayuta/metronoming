import curses

from .audio import stop_audio
from .config import BPM_MAX, BPM_MIN, load_bpm, save_bpm
from .metro import Metro

_STEP = 1

# 0 = tick なし (all beats same accent), 2-7 = time signature
_BEAT_MODES  = [0, 2, 3, 4, 5, 6, 7]
_BEAT_LABELS = {0: "tick なし", 2: "2 拍子", 3: "3 拍子", 4: "4 拍子",
                5: "5 拍子", 6: "6 拍子", 7: "7 拍子"}

# Reference line positions as fractions of swing:
#   center (0) + 4 on each side → 9 lines
#   ±1.0 = beat extremes, ±0.25/0.5/0.75 = 16th note subdivisions
_REF_FRACS = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]

# curses color-pair IDs
_C_REF    = 1   # green  : reference lines (non-center)
_C_CENTER = 2   # yellow : center reference line
_C_BAR    = 3   # cyan   : moving vertical bar
_C_PLAY   = 4   # green  : ▶ PLAYING label
_C_STOP   = 5   # red    : ■ STOPPED label
_C_BPM    = 6   # yellow : BPM / beat label


def _draw(stdscr: "curses._CursesWindow", bpm: int, pos: float,
          playing: bool, beat_label: str) -> None:
    rows, cols = stdscr.getmaxyx()
    stdscr.erase()
    mid = cols // 2

    use_color = curses.has_colors()

    def attr(pair: int, bold: bool = False) -> int:
        a = curses.color_pair(pair) if use_color else 0
        return a | curses.A_BOLD if bold else a

    # ── header ──────────────────────────────────────────────────────────
    bpm_str = f"BPM: {bpm}"
    try:
        stdscr.addstr(1, (cols - len(bpm_str)) // 2, bpm_str,
                      attr(_C_BPM, bold=True))
    except curses.error:
        pass

    beat_str = f"拍子: {beat_label}"
    try:
        stdscr.addstr(2, (cols - len(beat_str)) // 2, beat_str,
                      attr(_C_BPM))
    except curses.error:
        pass

    # ── pendulum area ────────────────────────────────────────────────────
    bar_top    = 4
    bar_bottom = rows - 4
    bar_height = bar_bottom - bar_top

    if bar_height > 0:
        swing = min(mid - 2, cols // 3)

        # 1. Reference lines (drawn first, moving bar overwrites on collision)
        for frac in _REF_FRACS:
            rx = mid + round(frac * swing)
            rx = max(0, min(rx, cols - 1))
            is_center = (frac == 0.0)
            line_attr = attr(_C_CENTER, bold=True) if is_center else attr(_C_REF)
            for row in range(bar_top, bar_bottom + 1):
                if 0 <= row < rows:
                    try:
                        stdscr.addch(row, rx, "|", line_attr)
                    except curses.error:
                        pass

        # 2. Moving vertical bar (drawn on top of reference lines)
        x = mid + round(pos * swing)
        x = max(1, min(x, cols - 2))
        bar_attr = attr(_C_BAR, bold=True)
        for row in range(bar_top, bar_bottom + 1):
            if 0 <= row < rows:
                try:
                    stdscr.addch(row, x, "|", bar_attr)
                except curses.error:
                    pass

    # ── footer ───────────────────────────────────────────────────────────
    if playing:
        status = "▶  PLAYING"
        st_attr = attr(_C_PLAY, bold=True)
    else:
        status = "■  STOPPED"
        st_attr = attr(_C_STOP, bold=True)
    try:
        stdscr.addstr(rows - 2, (cols - len(status)) // 2, status, st_attr)
    except curses.error:
        pass

    hint = "↑↓:BPM  ←→:拍子  SPACE:stop/start  q:quit"
    try:
        stdscr.addstr(rows - 1, (cols - len(hint)) // 2, hint)
    except curses.error:
        pass

    stdscr.refresh()


def run() -> None:
    bpm = load_bpm()
    metro = Metro(bpm)
    metro.start()
    playing = True
    beat_idx = 0

    def _main(stdscr: "curses._CursesWindow") -> None:
        nonlocal bpm, playing, beat_idx
        curses.curs_set(0)

        # Color initialization
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(_C_REF,    curses.COLOR_GREEN,  -1)
            curses.init_pair(_C_CENTER, curses.COLOR_YELLOW, -1)
            curses.init_pair(_C_BAR,    curses.COLOR_CYAN,   -1)
            curses.init_pair(_C_PLAY,   curses.COLOR_GREEN,  -1)
            curses.init_pair(_C_STOP,   curses.COLOR_RED,    -1)
            curses.init_pair(_C_BPM,    curses.COLOR_YELLOW, -1)

        stdscr.nodelay(True)
        stdscr.timeout(16)  # ~60 FPS

        while True:
            key = stdscr.getch()

            if key in (ord("q"), 27):
                break
            elif key == ord(" "):
                if playing:
                    metro.stop()
                    playing = False
                else:
                    metro.start()
                    playing = True
            elif key == curses.KEY_UP:
                bpm = min(BPM_MAX, bpm + _STEP)
                metro.set_bpm(bpm)
                save_bpm(bpm)
            elif key == curses.KEY_DOWN:
                bpm = max(BPM_MIN, bpm - _STEP)
                metro.set_bpm(bpm)
                save_bpm(bpm)
            elif key == curses.KEY_RIGHT:
                beat_idx = (beat_idx + 1) % len(_BEAT_MODES)
                metro.set_beat_mode(_BEAT_MODES[beat_idx])
            elif key == curses.KEY_LEFT:
                beat_idx = (beat_idx - 1) % len(_BEAT_MODES)
                metro.set_beat_mode(_BEAT_MODES[beat_idx])

            pos = metro.pendulum_pos() if playing else 0.0
            _draw(stdscr, bpm, pos, playing, _BEAT_LABELS[_BEAT_MODES[beat_idx]])

    try:
        curses.wrapper(_main)
    finally:
        metro.stop()
        stop_audio()
