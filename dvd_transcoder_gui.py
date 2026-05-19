import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


@dataclass
class DiscTrackInfo:
    title_number: int
    duration: str
    audio_tracks: list[str]
    subtitle_tracks: list[str]


class EncodeWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_with_result = pyqtSignal(bool, str)

    def __init__(self, command: list[str]):
        super().__init__()
        self.command = command

    def run(self):
        try:
            self.status.emit("変換開始...")
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            percent_pattern = re.compile(r"(\d{1,3}\.\d) %")

            if process.stdout is None:
                raise RuntimeError("進捗ストリームが取得できませんでした")

            for line in process.stdout:
                m = percent_pattern.search(line)
                if m:
                    value = int(float(m.group(1)))
                    self.progress.emit(max(0, min(100, value)))
                if "Encoding" in line or "%" in line:
                    self.status.emit(line.strip())

            code = process.wait()
            if code == 0:
                self.progress.emit(100)
                self.finished_with_result.emit(True, "変換が完了しました")
            else:
                self.finished_with_result.emit(False, f"変換に失敗しました (exit={code})")
        except Exception as e:
            self.finished_with_result.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DVD -> H.264 MP4 変換")
        self.setMinimumSize(720, 520)

        self.worker: EncodeWorker | None = None
        self.current_track: DiscTrackInfo | None = None

        central = QWidget()
        layout = QVBoxLayout(central)

        self.detect_label = QLabel("DVD状態: 未検知")
        self.refresh_button = QPushButton("DVD再検知")
        self.refresh_button.clicked.connect(self.detect_disc)

        top = QHBoxLayout()
        top.addWidget(self.detect_label)
        top.addStretch(1)
        top.addWidget(self.refresh_button)
        layout.addLayout(top)

        track_grid = QGridLayout()
        track_grid.addWidget(QLabel("保存先:"), 0, 0)
        self.output_edit = QLineEdit(str(Path.home() / "Videos" / "dvd_output.mp4"))
        browse_button = QPushButton("選択")
        browse_button.clicked.connect(self.select_output)
        track_grid.addWidget(self.output_edit, 0, 1)
        track_grid.addWidget(browse_button, 0, 2)

        track_grid.addWidget(QLabel("使用エンジン:"), 1, 0)
        self.engine_box = QComboBox()
        self.engine_box.addItems(["HandBrakeCLI", "ffmpeg"])
        self.engine_box.currentTextChanged.connect(self.update_controls_for_engine)
        track_grid.addWidget(self.engine_box, 1, 1)

        track_grid.addWidget(QLabel("タイトル番号:"), 2, 0)
        self.title_box = QComboBox()
        track_grid.addWidget(self.title_box, 2, 1)
        self.scan_button = QPushButton("タイトル情報を取得")
        self.scan_button.clicked.connect(self.scan_titles)
        track_grid.addWidget(self.scan_button, 2, 2)

        layout.addLayout(track_grid)

        self.audio_list = QListWidget()
        self.audio_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.subtitle_list = QListWidget()
        self.subtitle_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        streams = QHBoxLayout()
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("音声トラック選択"))
        left_col.addWidget(self.audio_list)
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("字幕トラック選択"))
        right_col.addWidget(self.subtitle_list)
        streams.addLayout(left_col)
        streams.addLayout(right_col)
        layout.addLayout(streams)

        self.subtitle_burn = QCheckBox("字幕を焼き込み(HandBrakeのみ)")
        layout.addWidget(self.subtitle_burn)

        self.progress = QProgressBar()
        self.status = QLabel("待機中")
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        action = QHBoxLayout()
        self.start_button = QPushButton("変換開始")
        self.start_button.clicked.connect(self.start_encode)
        action.addStretch(1)
        action.addWidget(self.start_button)
        layout.addLayout(action)

        self.setCentralWidget(central)

        self.detect_disc()
        self.update_controls_for_engine(self.engine_box.currentText())

    def detect_disc(self):
        mounted = self.find_mounted_dvd()
        if mounted:
            self.detect_label.setText(f"DVD状態: 検知 ({mounted})")
        else:
            self.detect_label.setText("DVD状態: 未検知 (/dev/sr0 を確認)")

    def find_mounted_dvd(self) -> str | None:
        candidates = ["/media", "/mnt", f"/run/media/{os.getenv('USER', '')}"]
        for c in candidates:
            p = Path(c)
            if not p.exists():
                continue
            for path in p.rglob("VIDEO_TS"):
                return str(path.parent)
        return None

    def scan_titles(self):
        source = self.find_mounted_dvd() or "/dev/sr0"
        cmd = ["HandBrakeCLI", "--scan", "-i", source]
        if shutil.which("HandBrakeCLI") is None:
            QMessageBox.critical(self, "エラー", "HandBrakeCLI が見つかりません")
            return
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = "\n".join([result.stdout or "", result.stderr or ""])
            titles = self.parse_titles(output)
            if not titles:
                QMessageBox.warning(self, "注意", "タイトル情報を取得できませんでした")
                return
            self.title_box.clear()
            for t in titles:
                self.title_box.addItem(f"{t.title_number}: {t.duration}", t)
            self.title_box.setCurrentIndex(0)
            self.load_stream_lists(titles[0])
            try:
                self.title_box.currentIndexChanged.disconnect(self.on_title_changed)
            except TypeError:
                pass
            self.title_box.currentIndexChanged.connect(self.on_title_changed)
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

    def on_title_changed(self, idx: int):
        item = self.title_box.itemData(idx)
        if item:
            self.load_stream_lists(item)

    def load_stream_lists(self, track: DiscTrackInfo):
        self.current_track = track
        self.audio_list.clear()
        self.subtitle_list.clear()
        for a in track.audio_tracks:
            self.audio_list.addItem(QListWidgetItem(a))
        for s in track.subtitle_tracks:
            self.subtitle_list.addItem(QListWidgetItem(s))

    def parse_titles(self, text: str) -> list[DiscTrackInfo]:
        titles = []
        title_pat = re.compile(r"\+ title (\d+):")
        duration_pat = re.compile(r"\+ duration: ([0-9:]+)")
        track_line_pat = re.compile(r"\+\s*(\d+),\s*(.+)$")

        current = None
        in_audio = False
        in_sub = False
        for raw in text.splitlines():
            line = raw.strip()
            tm = title_pat.match(line)
            if tm:
                if current:
                    titles.append(current)
                current = DiscTrackInfo(int(tm.group(1)), "??:??:??", [], [])
                in_audio = False
                in_sub = False
                continue
            if current is None:
                continue
            dm = duration_pat.match(line)
            if dm:
                current.duration = dm.group(1)
            if "audio tracks:" in line:
                in_audio = True
                in_sub = False
                continue
            if "subtitle tracks:" in line:
                in_audio = False
                in_sub = True
                continue
            if in_audio:
                am = track_line_pat.match(line)
                if am:
                    current.audio_tracks.append(f"{am.group(1)}: {am.group(2)}")
            if in_sub:
                sm = track_line_pat.match(line)
                if sm:
                    current.subtitle_tracks.append(f"{sm.group(1)}: {sm.group(2)}")

        if current:
            titles.append(current)
        return titles

    def update_controls_for_engine(self, engine: str):
        self.subtitle_burn.setEnabled(engine == "HandBrakeCLI")

    def select_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "保存先選択", self.output_edit.text(), "MP4 files (*.mp4)")
        if file_name:
            if not file_name.lower().endswith(".mp4"):
                file_name += ".mp4"
            self.output_edit.setText(file_name)

    def selected_track_ids(self, widget: QListWidget) -> list[str]:
        out = []
        for item in widget.selectedItems():
            out.append(item.text().split(":", 1)[0].strip())
        return out

    def build_command(self) -> list[str]:
        source = self.find_mounted_dvd() or "/dev/sr0"
        out_path = self.output_edit.text().strip()
        if not out_path:
            raise ValueError("保存先が未指定です")

        if self.engine_box.currentText() == "HandBrakeCLI":
            if shutil.which("HandBrakeCLI") is None:
                raise ValueError("HandBrakeCLI が見つかりません")
            title = self.current_track.title_number if self.current_track else 1
            cmd = [
                "HandBrakeCLI",
                "-i",
                source,
                "-o",
                out_path,
                "--format",
                "av_mp4",
                "--encoder",
                "x264",
                "--title",
                str(title),
            ]
            audio = self.selected_track_ids(self.audio_list)
            subs = self.selected_track_ids(self.subtitle_list)
            if audio:
                cmd += ["--audio", ",".join(audio)]
            if subs:
                cmd += ["--subtitle", ",".join(subs)]
                if self.subtitle_burn.isChecked():
                    cmd += ["--subtitle-burned"]
            return cmd

        if shutil.which("ffmpeg") is None:
            raise ValueError("ffmpeg が見つかりません")
        return [
            "ffmpeg",
            "-y",
            "-i",
            source,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            out_path,
        ]

    def start_encode(self):
        try:
            cmd = self.build_command()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))
            return

        self.progress.setValue(0)
        self.start_button.setEnabled(False)
        self.worker = EncodeWorker(cmd)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status.setText)
        self.worker.finished_with_result.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, ok: bool, message: str):
        self.start_button.setEnabled(True)
        self.status.setText(message)
        if ok:
            QMessageBox.information(self, "完了", message)
        else:
            QMessageBox.critical(self, "失敗", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
