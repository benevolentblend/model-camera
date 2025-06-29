import time
import os
import shutil
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from picamera2.previews.qt import QGlPicamera2


DISPLAY_WIDTH = 300
DISPLAY_HEIGHT = 200

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

SD_CARD_DIRECTORY = "/media/pi/PI-SD"
FOLDER_DIRECTORY = "/DCIM/100PICAM"


def is_sd_card_ready() -> bool:
    return os.path.isdir(SD_CARD_DIRECTORY)


def get_foldername():
    return f"{SD_CARD_DIRECTORY}{FOLDER_DIRECTORY}"


def get_filename():
    datetime_suffix = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"PIV{datetime_suffix}.mp4"


class AppWindow(QWidget):
    def __init__(self, camera: Picamera2, camera_preview: QGlPicamera2):

        super().__init__()
        self.recording = False
        self.camera = camera
        self.label = QLabel()
        self.current_file = ""

        self.label.setText("Standby")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(camera_preview, 90)
        layout.addWidget(self.label, 10)

        self.resize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.setLayout(layout)

        self.setFocusPolicy(Qt.StrongFocus)

    def start_recording(self):
        self.current_file = get_filename()
        encoder = H264Encoder(10000000)
        output = FfmpegOutput(self.current_file)
        self.camera.start_encoder(encoder, output)
        self.label.setText("Recording")

    def stop_recording(self):
        self.camera.stop_encoder()
        self.label.setText("Saving")
        input = f"{os.getcwd()}/{self.current_file}"
        output = f"{get_foldername()}/{self.current_file}"
        shutil.move(input, output)

        print(f"shutil.move('{input}', '{output}') ")

        os.system("sync")

        self.label.setText(f"Saved {self.current_file}")
        self.current_file = ""

    def keyPressEvent(self, event):

        key = event.key()

        if key == Qt.Key_R:
            self.recording = not self.recording

            if self.recording:
                self.start_recording()
            else:
                self.stop_recording()

        elif key == Qt.Key_Escape:
            self.close()  # Close the window on Escape key press


if __name__ == "__main__":
    if not is_sd_card_ready():
        print("SD card not detected!")
        exit(1)

    os.makedirs(get_foldername(), exist_ok=True)

    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"size": (VIDEO_WIDTH, VIDEO_HEIGHT)},
        lores={"size": (DISPLAY_WIDTH, DISPLAY_HEIGHT)},
        display="lores",
    )
    picam2.configure(video_config)

    app = QApplication([])

    qpicamera2 = QGlPicamera2(
        picam2, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, keep_ar=False
    )
    qpicamera2.setWindowFlag(QtCore.Qt.FramelessWindowHint)

    window = AppWindow(camera=picam2, camera_preview=qpicamera2)

    picam2.start()
    window.showFullScreen()
    app.exec()
