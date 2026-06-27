import math
import threading
import time

from .audio import play_click



class Metro:
    """Metronome timing and beat generation engine."""

    def __init__(self, bpm: int) -> None:
        self._lock = threading.Lock()
        self._bpm = bpm
        self._beat_mode = 0
        self._last = time.monotonic()
        self._total = 0
        self._running = False

    def set_bpm(self, bpm: int) -> None:
        with self._lock:
            self._bpm = bpm

    def set_beat_mode(self, mode: int) -> None:
        with self._lock:
            self._beat_mode = mode
            self._total = 0

    def start(self) -> None:
        if self._running:
            return  # Already running
        self._running = True
        self._last = time.monotonic()
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            with self._lock:
                interval = 60.0 / self._bpm
                mode = self._beat_mode
                now = time.monotonic()
                if now - self._last >= interval:
                    self._last += interval
                    n = self._total
                    self._total += 1
                    fired = True
                else:
                    fired = False
            if fired:
                accent = True if mode == 0 else (n % mode == 0)
                play_click(accent)
            time.sleep(0.001)

    def pendulum_pos(self) -> float:
        """Returns -1.0 (left) to +1.0 (right)."""
        with self._lock:
            interval = 60.0 / self._bpm
            last = self._last
            parity = self._total % 2
        t = max(0.0, min(time.monotonic() - last, interval))
        v = math.cos(math.pi * t / interval)
        return v if parity == 0 else -v
