import io
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

_RATE = 44100
_tmp_dir = Path(tempfile.mkdtemp(prefix="metronoming-"))

# Frequency analysis of a real mechanical metronome (YouTube: _0ADzsPg4Jc):
#   dominant: 3390 Hz, secondaries: 2660, 1890, 1690, 1040 Hz
#   attack peak at 5ms, plateau at 15-20ms (body ring), silent by 50ms

def _make_wav(freq: int, dur: float, vol: float, label: str) -> Path:
    """Generate click sound with given frequency and duration.

    Args:
        freq: Center frequency in Hz
        dur: Duration in seconds
        vol: Volume (0-1)
        label: Label for filename (e.g., 'bell' or 'click')
    """
    n = int(_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(42)

    # Attack envelope: 3ms rise
    attack = np.minimum(t / 0.003, 1.0)

    # Noise component (impacts)
    noise = rng.standard_normal(n) * np.exp(-t * 300)

    # Main tone: dominant frequency
    tone = np.sin(2 * np.pi * freq * t)

    # Harmonics for richer sound
    harmonics = (
        0.5 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.3 * np.sin(2 * np.pi * freq * 3 * t)
    )

    # Combine: more noise for click, more tone for bell
    if "bell" in label:
        # Bell: pure tone with harmonics, quick decay
        wave_data = (0.1 * noise + 0.7 * tone + 0.2 * harmonics) * attack * np.exp(-t * 200)
    else:
        # Click: woody, natural decay
        wave_data = (0.3 * noise + 0.5 * tone + 0.2 * harmonics) * attack * np.exp(-t * 100)

    peak = np.max(np.abs(wave_data))
    if peak > 0:
        wave_data = wave_data / peak * vol

    samples = (wave_data * 32767).astype(np.int16)
    path = _tmp_dir / f"click_{label}.wav"
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_RATE)
        wf.writeframes(samples.tobytes())
    path.write_bytes(buf.getvalue())
    return path


# Bell sound for accent beats (high frequency, short decay)
_HIGH = _make_wav(freq=1800, dur=0.04, vol=0.9, label="bell")

# Click sound for normal beats (low frequency, longer decay)
_LOW = _make_wav(freq=500, dur=0.06, vol=0.8, label="click")


def play_click(accent: bool = False) -> None:
    path = _HIGH if accent else _LOW
    try:
        subprocess.Popen(
            ["aplay", "-q", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def stop_audio() -> None:
    pass
