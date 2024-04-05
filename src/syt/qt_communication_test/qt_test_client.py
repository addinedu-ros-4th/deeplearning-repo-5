import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6 import uic
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import cv2
import numpy as np
import time

# Load UI file
from_class = uic.loadUiType("/home/addinedu/dev_ws/DLProject/mar18/socket/qt_test.ui")[0]

def recvall(sock, count):
    buf = b''

    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf


class Camera(QThread):
    update = pyqtSignal()

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running =  True

    def run(self):
        count = 0
        while self.running == True:
            self.update.emit()          # 시그널을 발생시키는 함수.
            time.sleep(0.1)
    
    def stop(self):
        self.running = False


class VideoThread(QThread):
    change_server_pixmap_signal = pyqtSignal(np.ndarray)
    change_client_pixmap_signal = pyqtSignal(np.ndarray)
    
    def run(self):
        TCP_IP = '192.168.0.15'
        TCP_PORT = 5005

        sock = socket.socket()
        sock.connect((TCP_IP, TCP_PORT))

        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_string = cv2.imencode('.jpg', frame)[1].tostring()
            size = len(frame_string)
            sock.sendall(str(size).ljust(16).encode())
            sock.sendall(frame_string)
            length = int(sock.recv(16).strip())
            print("Receiving frame of size:", length)
            frame_string = recvall(sock, length)
            frame_array = np.frombuffer(frame_string, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            self.change_server_pixmap_signal.emit(frame)  # Emit the frame to update server webcam label
            if cv2.waitKey(1) & 0xFF == 27:
                break

        sock.close()
        cv2.destroyAllWindows()




class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.video_thread = VideoThread()
        self.video_thread.change_server_pixmap_signal.connect(self.update_server_image)
        self.video_thread.change_client_pixmap_signal.connect(self.update_client_image)
        self.video_thread.start()



    def update_camera_image(self):
        retval, image = self.video.read()

        if retval:
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.setImage()


    def setImage(self):
        h, w, c = self.image.shape
        qimage = QImage(self.image.data, w, h, w*c, QImage.Format.Format_BGR888)
        self.pixmap = self.pixmap.fromImage(qimage)
        self.pixmap = self.pixmap.scaled(self.label.width(), self.label.height())
        self.label2.setPixmap(self.pixmap)



    def update_server_image(self, frame):
        """Updates the image shown in the server webcam label."""
        qt_img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)
        self.label.setPixmap(pixmap)



    def update_client_image(self, frame):
        """Updates the image shown in the client webcam label."""
        qt_img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)
        self.label2.setPixmap(pixmap)



if __name__ == "__main__":
    app = QApplication(sys.argv)  # 프로그램 실행
    myWindows = WindowClass()     # 화면 클래스 생성
    myWindows.show()              # 프로그램 화면 보이기
    sys.exit(app.exec())          # 프로그램을 종료까지 동작시킴

