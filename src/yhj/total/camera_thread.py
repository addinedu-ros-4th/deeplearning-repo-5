# camera_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import cv2
import time
from queue import Queue

camera_image_queue = Queue(maxsize=1)  # 이미지를 저장하는 이미지 큐

class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, HTT):
        super().__init__()
        self.HTT = HTT  # HTT 객체를 CameraThread의 속성으로 전달받음

    def run(self):
        cap = cv2.VideoCapture(0)
        last_image_time = time.time()

        while True:
            ret, cv_img = cap.read()
            if ret:
                current_time = time.time()
                if not camera_image_queue.empty():
                    camera_image_queue.get()
                if current_time - last_image_time >= 0.05:
                    camera_image_queue.put(cv_img)
                    last_image_time = current_time

                cv_img = cv2.flip(cv_img, 1)
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                
                height, width, channel = cv_img.shape

                aspect_ratio = 160 / width
                resized_img = cv2.resize(cv_img, (160, int(height * aspect_ratio)))

                qt_img = QImage(resized_img.data, 160, int(height * aspect_ratio), QImage.Format.Format_RGB888)
                self.change_pixmap_signal.emit(qt_img)
                
    def stop(self):
        self._is_running = False
