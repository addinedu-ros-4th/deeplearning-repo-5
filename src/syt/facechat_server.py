import cv2
import socket
import struct
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
import sys
from vidstream import StreamingServer, AudioReceiver, CameraClient, AudioSender
from PyQt6 import uic
import pickle


class StreamingServerModified(QObject):
    frame_updated = pyqtSignal(QPixmap)

    def __init__(self, host, port, slots=8, quit_key='q'):
        super().__init__()
        self.__host = host
        self.__port = port
        self.__slots = slots
        self.__used_slots = 0
        self.__running = False
        self.__quit_key = quit_key
        self.__block = threading.Lock()
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__init_socket()

    def __init_socket(self):
        self.__server_socket.bind((self.__host, self.__port))

    def start_server(self):
        if self.__running:
            print("Server is already running")
        else:
            self.__running = True
            server_thread = threading.Thread(target=self.__server_listening)
            server_thread.start()

    def __server_listening(self):
        self.__server_socket.listen()
        while self.__running:
            self.__block.acquire()
            connection, address = self.__server_socket.accept()
            if self.__used_slots >= self.__slots:
                print("Connection refused! No free slots!")
                connection.close()
                self.__block.release()
                continue
            else:
                self.__used_slots += 1
            self.__block.release()
            thread = threading.Thread(target=self.__client_connection, args=(connection, address,))
            thread.start()

    def stop_server(self):
        if self.__running:
            self.__running = False
            closing_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            closing_connection.connect((self.__host, self.__port))
            closing_connection.close()
            self.__block.acquire()
            self.__server_socket.close()
            self.__block.release()
        else:
            print("Server not running!")

    def __client_connection(self, connection, address):
        payload_size = struct.calcsize('>L')
        data = b""

        while self.__running:

            break_loop = False

            while len(data) < payload_size:
                received = connection.recv(4096)
                if received == b'':
                    connection.close()
                    self.__used_slots -= 1
                    break_loop = True
                    break
                data += received

            if break_loop:
                break

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]

            msg_size = struct.unpack(">L", packed_msg_size)[0]

            while len(data) < msg_size:
                data += connection.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            qImg = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(qImg)
            self.frame_updated.emit(pixmap)
            if cv2.waitKey(1) == ord(self.__quit_key):
                connection.close()
                self.__used_slots -= 1
                break


from_class = uic.loadUiType("/home/addinedu/dev_ws/DLProject/final_src/final/facechat.ui")[0]

# 나머지 코드
class FaceChatWindow(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("server")
        
        # Port number configuration
        self.local_ip_address = '192.168.0.31'
        self.client_ip = '192.168.0.15'
        self.vid_recv_port = 6001
        self.aud_recv_port = 6002
        self.vid_send_port = 6003
        self.aud_send_port = 6004

        # 이벤트 설정 
        self.gestureButton.clicked.connect(self.startCommunication)

        # vid recv 
        self.stream_recv = StreamingServerModified(self.local_ip_address, self.vid_recv_port)
        self.stream_recv.frame_updated.connect(self.update_pixmap)
        self.stream_recv_thread = QThread()
        self.stream_recv.moveToThread(self.stream_recv_thread)
        self.stream_recv_thread.started.connect(self.stream_recv.start_server)
        self.stream_recv_thread.start()


    def startCommunication(self):
        # audio recv
        audio_recv = AudioReceiver(self.local_ip_address, self.aud_recv_port)   
        t2 = threading.Thread(target=audio_recv.start_server)
        t2.daemon = True
        t2.start()

        # vid send
        camera_client = CameraClient(self.client_ip, self.vid_send_port)
        t3 = threading.Thread(target=camera_client.start_stream)
        t3.daemon = True
        t3.start()

        # audio send
        audio_sender = AudioSender(self.client_ip, self.aud_send_port)
        t4 = threading.Thread(target=audio_sender.start_stream)
        t4.daemon = True
        t4.start()

    def update_pixmap(self, pixmap):
        self.chatpixmap.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = FaceChatWindow()
    myLogin.show()
    sys.exit(app.exec())