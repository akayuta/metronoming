import io
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

_RATE = 44100
_tmp_dir = Path(tempfile.mkdtemp(prefix="metronoming-"))

def _make_wav(freq: int, dur: float, vol: float, label: str) -> Path:
    """Generate click sound with given frequency and duration.

    Args:
        freq: Center frequency in Hz
        dur: Duration in seconds
        vol: Volume (0-1)
        label: Label for filename (e.g., 'bell' or 'click')
    """
    n = int(_RATE * dur)
    samples = []

    for i in range(n):
        t = i / _RATE

        # Attack envelope: 3ms rise
        attack = min(t / 0.003, 1.0)

        # Decay
        if "bell" in label:
            decay = math.exp(-t * 200)
        else:
            decay = math.exp(-t * 100)

        # Main tone
        tone = math.sin(2 * math.pi * freq * t)

        # Harmonics
        harm2 = 0.5 * math.sin(2 * math.pi * freq * 2 * t)
        harm3 = 0.3 * math.sin(2 * math.pi * freq * 3 * t)

        # Combine
        if "bell" in label:
            sample = (0.7 * tone + 0.2 * (harm2 + harm3)) * attack * decay
        else:
            sample = (0.5 * tone + 0.2 * (harm2 + harm3)) * attack * decay

        # Apply volume and convert to int16
        sample = int(sample * vol * 32767)
        sample = max(-32768, min(32767, sample))
        samples.append(sample)

    path = _tmp_dir / f"click_{label}.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_RATE)
        wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
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
