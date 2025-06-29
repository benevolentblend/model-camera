import time
import os
import shutil
from datetime import datetime
from gpiozero import Button

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QWaitCondition, QMutex


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

mutex = QMutex()


def is_sd_card_ready() -> bool:
    return os.path.isdir(SD_CARD_DIRECTORY)


def get_foldername():
    return f"{SD_CARD_DIRECTORY}{FOLDER_DIRECTORY}"


def get_filename():
    datetime_suffix = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"PIV{datetime_suffix}.mp4"


class ButtonWorker(QObject):
    button_press = pyqtSignal()

    def __init__(self, safe_to_record: QWaitCondition):
        super().__init__()
        self.safe_to_record = safe_to_record

    def run(self):
        button = Button(21)
        while True:
            # Wait to start recording.
            # It is safe to start recording right away.
            button.wait_for_press()
            self.button_press.emit()
            button.wait_for_release()

            # Wait to stop recording.
            # We must wait for the button to be release,
            # or else we will could have a race condition where
            # we receive our safe_to_record condition before 
            # the button is released.
            button.wait_for_press()
            button.wait_for_release()

            self.button_press.emit()

            # Wait for video to be saved
            self.safe_to_record.wait(mutex)
            
            # Ensure we are not waking up in a bad state
            if button.is_pressed:
                button.wait_for_release()


class AppWindow(QWidget):
    recording = False

    def __init__(self, camera: Picamera2, camera_preview: QGlPicamera2):

        super().__init__()

        self.camera = camera
        self.safe_to_record = QWaitCondition()
        self.label = QLabel()
        self.current_file = ""
        self.button_thread = QThread()
        self.button_worker = ButtonWorker(safe_to_record=self.safe_to_record)
        self.button_worker.moveToThread(self.button_thread)
        self.button_thread.started.connect(self.button_worker.run)
        self.button_worker.button_press.connect(self.record_toggle)

        self.label.setText("Standby")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(camera_preview, 90)
        layout.addWidget(self.label, 10)

        self.resize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.setLayout(layout)

        self.setFocusPolicy(Qt.StrongFocus)
        self.button_thread.start()

    def start_recording(self):
        self.current_file = get_filename()
        encoder = H264Encoder(10000000)
        output = FfmpegOutput(self.current_file)
        self.camera.start_encoder(encoder, output)
        self.label.setText("Recording")

    def stop_recording(self):
        self.label.setText("Saving")
        self.camera.stop_encoder()

        input = f"{os.getcwd()}/{self.current_file}"
        output = f"{get_foldername()}/{self.current_file}"
        shutil.move(input, output)

        # Needed to ensure file is written to SD card
        os.system("sync")

        self.label.setText(f"Saved {self.current_file}")
        self.current_file = ""
        time.sleep(5)
        self.safe_to_record.wakeAll()

    def record_toggle(self):
        self.recording = not self.recording

        if self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def keyPressEvent(self, event):

        key = event.key()

        if key == Qt.Key_R:
            self.record_toggle()

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
    qpicamera2.setWindowFlag(Qt.FramelessWindowHint)

    window = AppWindow(camera=picam2, camera_preview=qpicamera2)

    picam2.start()
    window.showFullScreen()
    app.exec()
