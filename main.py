import sys
import cv2
import csv
import os
from collections import Counter
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtMultimedia import QSoundEffect

# Initialize sound effects
beep = QSoundEffect()
error_sound = QSoundEffect()
if os.path.exists("beep.wav"):
    beep.setSource(QUrl.fromLocalFile(os.path.abspath("beep.wav")))
if os.path.exists("error-10.wav"):
    error_sound.setSource(QUrl.fromLocalFile(os.path.abspath("error-10.wav")))

class QRScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Scanner - PyQt5 Edition")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #2e2e2e; color: #f0f0f0;")

        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #1e1e1e; color: #a0ffa0;")

        self.scan_count_label = QLabel("Scanned: 0")
        self.error_count_label = QLabel("Errors: 0")
        self.letter_freq_label = QLabel("Letter Frequencies: {}")

        self.select_csv_btn = QPushButton("Select CSV File")
        self.select_csv_btn.clicked.connect(self.select_csv_file)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)

        self.reset_btn = QPushButton("Reset Counters")
        self.reset_btn.clicked.connect(self.reset_counters)

        self.select_beep_btn = QPushButton("Select Beep Sound")
        self.select_beep_btn.clicked.connect(self.select_beep_sound)

        self.select_error_btn = QPushButton("Select Error Sound")
        self.select_error_btn.clicked.connect(self.select_error_sound)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.scan_count_label)
        layout.addWidget(self.error_count_label)
        layout.addWidget(self.letter_freq_label)
        layout.addWidget(self.log)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.select_csv_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        sound_layout = QHBoxLayout()
        sound_layout.addWidget(self.select_beep_btn)
        sound_layout.addWidget(self.select_error_btn)
        layout.addLayout(sound_layout)

        self.setLayout(layout)

        self.csv_file = "output.csv"
        self.seen_data = set()
        self.first_letter_counts = Counter()
        self.error_count = 0

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Name Card ID', 'Last Name', 'First Name', 'School', 'Session'])

        self.cap = cv2.VideoCapture(0)
        self.qr_detector = cv2.QRCodeDetector()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def select_csv_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if path:
            self.csv_file = path

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(self.csv_file, 'r') as src, open(path, 'w', newline='') as dst:
                    dst.write(src.read())
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", str(e))

    def reset_counters(self):
        self.seen_data.clear()
        self.first_letter_counts.clear()
        self.error_count = 0
        self.log.clear()
        self.update_labels()

    def select_beep_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Beep Sound", "", "WAV Files (*.wav)")
        if path:
            beep.setSource(QUrl.fromLocalFile(path))

    def select_error_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Error Sound", "", "WAV Files (*.wav)")
        if path:
            error_sound.setSource(QUrl.fromLocalFile(path))

    def update_labels(self):
        self.scan_count_label.setText(f"Scanned: {len(self.seen_data)}")
        self.error_count_label.setText(f"Errors: {self.error_count}")
        self.letter_freq_label.setText(f"Letter Frequencies: {dict(self.first_letter_counts)}")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.error_count += 1
            if error_sound.isLoaded():
                error_sound.play()
            self.update_labels()
            return

        data, bbox, _ = self.qr_detector.detectAndDecode(frame)
        if data and data not in self.seen_data:
            fields = data.strip().split(',')
            if len(fields) == 5:
                self.seen_data.add(data)
                with open(self.csv_file, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(fields)

                last_name = fields[1].strip()
                if last_name:
                    first_char = last_name[0].upper()
                    if first_char.isalpha():
                        self.first_letter_counts[first_char] += 1

                if beep.isLoaded():
                    beep.play()

                self.log.append(f"\u2714 {data}")
            else:
                self.error_count += 1
                self.log.append(f"\u274c Malformed: {data}")
                if error_sound.isLoaded():
                    error_sound.play()
            self.update_labels()

        # Draw bounding box
        if bbox is not None and len(bbox) > 0:
            for i in range(len(bbox)):
                pt1 = tuple(map(int, bbox[i][0]))
                pt2 = tuple(map(int, bbox[(i+1) % len(bbox)][0]))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = QRScannerApp()
    main_window.show()
    sys.exit(app.exec_())