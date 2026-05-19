# DVD to MP4 GUI (Ubuntu, Python + PyQt)

Ubuntu向けのDVD自動検知・MP4(H.264)変換GUIアプリです。

## 機能
- DVD挿入後の再検知ボタンによる自動検知（`VIDEO_TS`マウントを探索）
- `HandBrakeCLI` または `ffmpeg` を使った H.264 MP4 変換
- 保存先の選択
- 進捗バー表示（HandBrakeCLIの出力からパース）
- 音声トラック / 字幕トラック選択（HandBrakeCLIスキャン結果に基づく）
- 字幕焼き込みオプション

## 事前準備
```bash
sudo apt update
sudo apt install -y handbrake-cli ffmpeg python3-pyqt6
```

## 実行
```bash
python3 dvd_transcoder_gui.py
```

## 使い方
1. DVDを挿入して「DVD再検知」。
2. 「タイトル情報を取得」を押す（HandBrakeCLIで解析）。
3. 必要に応じて音声・字幕トラックを選択。
4. 保存先を選んで「変換開始」。

## 注意
- CSS解除されていない市販DVD等の暗号化ディスクは別途ライブラリが必要な場合があります。
- `ffmpeg` モードでは簡易変換のみで、トラック詳細選択はHandBrakeCLIを推奨します。
