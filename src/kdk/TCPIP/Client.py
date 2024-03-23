import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QImage, QPixmap
from PyQt6 import uic
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import numpy as np
import cv2


# Load UI file
from_class = uic.loadUiType("/home/kkyu/amr_ws/DL/project_deep/face_communication/communication.ui")[0]

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def run(self):
        TCP_IP = '127.0.1.1'
        TCP_PORT = 3001

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))

        while True:
            length = int(s.recv(16).strip())
            print("Receiving frame of size:", length)
            
            frame_string = recvall(s, length)
            
            frame_array = np.frombuffer(frame_string, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            self.change_pixmap_signal.emit(frame)

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()

    def update_image(self, frame):
        qt_img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.video_thread.quit()
        self.video_thread.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec())
