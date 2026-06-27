# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 概要
  本プロジェクトはCLIでメトロノームアプリを作成するものです。
  
# 仕様
## UI
- metronomingというコマンド名で起動する。
- 起動したら前回指定したBPMを表示し、メトロノームを鳴らす
- 起動後は左右キーでBPMを変え、変化したBPMを画面表示する。
- 画面上に縦直線を左右に機械式メトロノーム分銅の動きを再現する。
- BPMを変化させたら~/.config/mtronoming.cfgに記録し、次回起動時に前回終了時と同じBPMで起動する。

## プログラム仕様
- LinuxのCLIで動作すること。

## 操作キー

| キー | 動作 |
|---|---|
| ↑ / ↓ | BPM ±1 |
| ← / → | 拍子切替（tick なし → 2 → 3 → 4 → 5 → 6 → 7 → …） |
| SPACE | ストップ / スタート |
| q / ESC | 終了 |

## 開発環境・コマンド

### Linux CLI
```bash
uv venv
uv pip install -e .
.venv/bin/metronoming
```

### Kivy (デスクトップ + Android)
```bash
# デスクトップテスト
uv pip install kivy
.venv/bin/python -m metronoming  # Kivy UI起動

# Android APK ビルド (buildozer 必須)
pip install buildozer
buildozer android debug
buildozer android release  # 本番 APK
```

## アーキテクチャ

```
metronoming/
├── __main__.py   # エントリポイント：Kivy 優先、フォールバック→ tui.run()
├── metro.py      # Metro クラス：BPM + 拍子モード制御、ビート生成スレッド
├── audio.py      # クリック音生成（numpy で WAV + aplay / sounddevice）
├── config.py     # ~/.config/mtronoming.cfg 読み書き（Android 対応）
├── tui.py        # curses TUI（Linux CLI 版）
└── main.py       # Kivy UI（デスクトップ＆ Android）
```

### UI バージョン
- **CLI (Linux)**: `tui.py` — キー操作（↑↓↑→：BPM/拍子、SPC：再開/停止）
- **GUI (Kivy)**: `main.py` — タッチ操作（スライダー、ボタン、Canvas アニメーション）

### 主要な設計判断

- **音声再生**: `aplay` サブプロセス方式を採用。`simpleaudio` / `sounddevice` は Linux 環境でスレッド競合によりセグメンテーションフォルトが発生したため。WAV ファイルは起動時に `/tmp/metronoming-*/` に生成し、以降 `aplay -q` で再生する。
- **振り子表示**: 垂直バー `O|||||` が `cos` 波に従い左右に水平スライド。`swing = min(mid-2, cols//3)` で振れ幅を決定。
- **振り子タイミング**: `_Metro._last`（直前ビート時刻）と `_Metro._total`（累計ビート数）から `cos(π * elapsed / interval)` でリアルタイムに位置を算出。偶数ビートは右→左、奇数は左→右にスイング。
- **TUI 更新**: `stdscr.timeout(16)`（約 60 FPS）で `getch()` をブロックさせて描画ループを回す。
- **BPM 範囲**: 20〜300 BPM。↑↓キーで ±1 BPM ずつ変化。
- **拍子モード**: `_BEAT_MODES = [0, 2, 3, 4, 5, 6, 7]`（0=tick なし）。←→で循環選択。`mode==0` は全ビートにアクセント、`mode>0` は `total % mode == 0` のビートにアクセント。拍子切替時に `_total` をリセット。
- **設定ファイル**: `~/.config/mtronoming.cfg`（`bpm=<値>` 形式）。BPM 変化のたびに即時書き込み。
