import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window

from .metro import Metro
from .config import BPM_MAX, BPM_MIN, load_bpm, save_bpm
from .audio import stop_audio

Window.size = (400, 800)

BEAT_MODES = [0, 2, 3, 4, 5, 6, 7]
BEAT_LABELS = {0: "Free", 2: "2beat", 3: "3beat", 4: "4beat",
               5: "5beat", 6: "6beat", 7: "7beat"}


class PendulumDisplay(Widget):
    """Canvas-based pendulum visualization."""

    def __init__(self, metro, **kwargs):
        super().__init__(**kwargs)
        self.metro = metro
        self.bind(size=self._on_size)
        Clock.schedule_interval(self._update, 0.016)  # ~60 FPS

    def _on_size(self, *args):
        self._update(0)

    def _update(self, dt):
        if self.width == 0 or self.height == 0:
            return

        self.canvas.clear()
        with self.canvas:
            self._draw_pendulum()

    def _draw_pendulum(self):
        w = self.width
        h = self.height
        mid_x = w / 2
        mid_y = h / 2

        pos = self.metro.pendulum_pos()
        swing = min(mid_x - 30, 100)
        bar_x = mid_x + pos * swing

        # Draw 9 timing lines: center (yellow) + left/right 4 (green/red alternating)
        ref_fracs = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
        for frac in ref_fracs:
            bx = mid_x + frac * swing
            if frac == 0.0:
                Color(1, 1, 0, 0.9)  # Yellow center
                width = 2
            else:
                Color(0, 0.8, 0, 0.7)  # Green side marks
                width = 1
            Line(points=[bx, mid_y + 10, bx, mid_y + 120], width=width)

        # Draw moving vertical bar (cyan)
        Color(0, 1, 1, 1)
        Line(points=[bar_x, mid_y - 100, bar_x, mid_y + 100], width=4)

        # Draw bob (weight) at bottom
        Color(0, 1, 1, 0.9)
        Ellipse(pos=(bar_x - 12, mid_y + 88), size=(24, 24))


class MetronomeApp(App):
    """Main Kivy application for Metronome."""

    def build(self):
        self.title = "Metronoming"
        self.bpm = load_bpm()
        self.beat_idx = 0
        self.metro = Metro(self.bpm)
        self.playing = True
        self.metro.start()

        # Root layout
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Header: BPM display + slider
        bpm_layout = BoxLayout(orientation="vertical", size_hint_y=0.12)
        self.bpm_label = Label(
            text=f"BPM: {self.bpm}",
            font_size="28sp",
            color=(1, 1, 0, 1),
        )
        bpm_layout.add_widget(self.bpm_label)

        bpm_slider = Slider(
            min=BPM_MIN,
            max=BPM_MAX,
            value=self.bpm,
            size_hint_y=0.5,
        )
        bpm_slider.bind(value=self._on_bpm_change)
        bpm_layout.add_widget(bpm_slider)
        root.add_widget(bpm_layout)

        # Pendulum display (larger)
        self.pendulum = PendulumDisplay(self.metro, size_hint_y=0.55)
        root.add_widget(self.pendulum)

        # Beat mode selection (buttons in grid)
        beat_layout = GridLayout(cols=7, size_hint_y=0.12, spacing=3)
        self.beat_buttons = []
        for i, mode in enumerate(BEAT_MODES):
            btn = Button(text=BEAT_LABELS[mode], font_size="10sp")
            btn.bind(on_press=lambda x, idx=i: self._on_beat_mode(x, idx))
            if i == 0:
                btn.background_color = (0, 1, 0, 0.8)  # Highlight initial
            self.beat_buttons.append(btn)
            beat_layout.add_widget(btn)
        root.add_widget(beat_layout)

        # Control buttons (Play/Stop)
        control_layout = BoxLayout(size_hint_y=0.15, spacing=10)

        self.play_btn = Button(text="STOP", font_size="20sp", background_color=(0, 1, 0, 0.8))
        self.play_btn.bind(on_press=self._toggle_play)
        control_layout.add_widget(self.play_btn)

        root.add_widget(control_layout)

        return root

    def _on_bpm_change(self, slider, value):
        self.bpm = int(value)
        self.bpm_label.text = f"BPM: {self.bpm}"
        self.metro.set_bpm(self.bpm)
        save_bpm(self.bpm)

    def _on_beat_mode(self, button, idx):
        # Update button highlights
        for i, btn in enumerate(self.beat_buttons):
            if i == idx:
                btn.background_color = (0, 1, 0, 0.8)  # Green
            else:
                btn.background_color = (1, 1, 1, 1)  # White
        # Set mode
        self.beat_idx = idx
        self.metro.set_beat_mode(BEAT_MODES[idx])

    def _toggle_play(self, *args):
        try:
            if self.playing:
                self.metro.stop()
                self.play_btn.text = "PLAY"
                self.play_btn.background_color = (1, 0, 0, 0.8)  # Red
                self.playing = False
            else:
                self.metro.start()
                self.play_btn.text = "STOP"
                self.play_btn.background_color = (0, 1, 0, 0.8)  # Green
                self.playing = True
        except Exception as e:
            print(f"Error in _toggle_play: {e}")
            import traceback
            traceback.print_exc()

    def on_stop(self):
        self.metro.stop()
        stop_audio()


def main():
    app = MetronomeApp()
    app.run()


if __name__ == "__main__":
    main()
