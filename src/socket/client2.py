import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QIcon, QImage, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from vidstream import StreamingServer, AudioReceiver, CameraClient, AudioSender
import socket
import subprocess
import re
import struct
from threading import Thread
import json
import cv2
import numpy as np
import threading
import pickle
import time

SERVER_IP = '192.168.0.31'
SERVER_PORT = 15031


def recvall(sock, count):
    buf = b''

    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

# Function to get IP address from ifconfig command in terminal
def get_ip_address(interface):
    try:
        # ifconfig 명령어 실행
        output = subprocess.check_output(["ifconfig", interface]).decode()
        # IP 주소 추출
        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
        if ip_match:
            ip_address = ip_match.group(1)
            return ip_address
        else:
            return None
    except subprocess.CalledProcessError:
        return None

# Login UI
from_class_login = uic.loadUiType("login.ui")[0]

class LoginUI(QMainWindow, from_class_login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("WELCOME")
        # ip주소 표시
        self.hostIP = get_ip_address("wlo1")
        self.labelIP.setText(str(self.hostIP))

        self.setWindowIcon(QIcon('addinedu.png'))

        pixmap = QPixmap('background.jpg')
        self.labelpixmap.setPixmap(pixmap)

        pixmap2 = QPixmap('client.png')
        scaled_pixmap2 = pixmap2.scaled(self.label3.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.label3.setPixmap(scaled_pixmap2)

        self.nameEdit.setStyleSheet("QLineEdit { border-radius: 6px; }")
        self.labelIP.setStyleSheet("QLineEdit { border-radius: 6px; }")

        # 이벤트 설정 
        self.loginBtn.clicked.connect(self.connectServer)
        self.nameEdit.returnPressed.connect(self.connectServer)

        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# data 보내는 함수
    def connectServer(self):
        self.userName = self.nameEdit.text()
        if self.userName:
            try:
                message = f"{self.userName}"
                self.sock.connect((SERVER_IP, SERVER_PORT))
                self.sock.sendall(message.encode())
                self.clientUI = ClientUI(self.userName, self.sock, SERVER_IP)  # 수정된 부분: 서버 IP 전달
                self.clientUI.show()
                self.close()  # Close the login dialog
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", f"{e}")
        else:
            QMessageBox.critical(self, "Error", "Please enter a username.")



# Client UI
from_class_client = uic.loadUiType("client.ui")[0]

# Inside your ClientUI class
class ClientUI(QDialog, from_class_client):
    data_received = pyqtSignal(str)

    def __init__(self, userName, sock, serverIP):  
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("화상 채팅 인터페이스")
        self.sock = sock
        self.userName = userName
        self.server_ip = serverIP
        self.serverip.setText(self.server_ip)

        # 서버에서 전송한 데이터를 받기 위한 스레드 시작
        self.receive_thread = Thread(target=self.receiveServerData)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.data_received.connect(self.updateTableWidget)

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget.setStyleSheet("QTableWidget { background-color: #f0f0f0; }"
                                        "QTableWidget QTableWidget::item { color: #333333; }"
                                        "QTableWidget QTableWidget::item:selected { background-color: #b8daff; }"
                                        "QTableWidget QHeaderView::section { background-color: #007bff; color: white; }"
                                        "QTableWidget QTableWidget::item { padding: 5px; }")

        self.setStyleSheet("""
            QPushButton#connectButton {
                background-color: #FFAAAA; /* slightly darker red */
            }
        """)

        
        self.callButton.clicked.connect(self.openFaceChatWindow)

    def receiveServerData(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if data:
                    # Emit the signal with the received data
                    self.data_received.emit(data)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break


    def updateTableWidget(self, data):
        try:
            data_dict = json.loads(data)
            # 테이블 초기화
            self.tableWidget.setRowCount(0)
            # JSON 데이터를 테이블 위젯에 추가
            for row, item in enumerate(data_dict["items"]):
                self.tableWidget.insertRow(row)
                for column, value in enumerate(item):
                    self.tableWidget.setItem(row, column, QTableWidgetItem(str(value)))
                # 버튼 생성
                button = QPushButton("Connect")
                button.setObjectName("connectButton")  # Set object name for styling
                if button:
                    # Connect button click only if button is properly initialized
                    button.clicked.connect(lambda _, row=row: self.connectButtonClicked(row))
                    # 셀 위젯으로 버튼 추가
                    self.tableWidget.setCellWidget(row, len(item), button)
                else:
                    print("Error: Button not properly initialized.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data: {e}")


    def connectButtonClicked(self, row):
        # Get the IP address and port number from the corresponding row
        ip_address_item = self.tableWidget.item(row, 0)
        port_item = self.tableWidget.item(row, 1)
        
        if ip_address_item is not None and port_item is not None:
            ip_address = ip_address_item.text()
            port_number = port_item.text()
            
            # Update the clientip and clientport labels
            self.clientip.setText(ip_address)
            self.clientport.setText(port_number)
        else:
            print("No IP address or port number found for this row.")


    def openFaceChatWindow(self):
        ip_address = self.clientip.text()
        port_number = int(self.clientport.text())
        self.facechat_window = FaceChatWindow(ip_address, port_number)
        self.facechat_window.show()



class FaceChatWindow(QDialog):
    def __init__(self, ip_address, port_number):
        super().__init__()
        uic.loadUi("facechat.ui", self)

        self.hostIP = get_ip_address("wlo1")
        self.local_ip_address = self.hostIP
        self.client_ip = ip_address
        self.vid_recv_port = 8002
        self.vid_send_port = 8001
        self.aud_recv_port = 8004
        self.aud_send_port = 8003

        self.toggle = 0

        # vid recv (서버 설정)
        self.stream_recv = StreamingServerModified(self.local_ip_address, self.vid_recv_port)
        self.stream_recv.frame_updated.connect(self.update_pixmap)
        self.stream_recv_thread = QThread()
        self.stream_recv.moveToThread(self.stream_recv_thread)
        self.stream_recv_thread.started.connect(self.stream_recv.start_server)
        self.stream_recv_thread.start()

        # audio recv (서버설정)
        self.audio_recv = AudioReceiver(self.local_ip_address, self.aud_recv_port)   
        t2 = threading.Thread(target=self.audio_recv.start_server)
        t2.daemon = True
        time.sleep(0.1)  # 1초 지연
        t2.start()


        self.text_recv_port = 8006
        self.text_send_port = 8005

        # 이벤트 설정
        self.gestureButton.clicked.connect(self.startCommunication)
        self.inputButton.clicked.connect(self.sendMessage)
        self.lineEdit.returnPressed.connect(self.sendMessage)

        if self.toggle == 1:
            self.myvideo_thread.frame_updated.connect(self.updateMyImage)


        # text recv (서버설정)
        self.text_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_recv.bind((self.local_ip_address, self.text_recv_port))
        self.text_recv.listen(True)

        t_accept = threading.Thread(target=self.accept_client)
        t_accept.daemon = True
        t_accept.start()
        

    def accept_client(self):
        self.client_socket, address = self.text_recv.accept()
        t5 = threading.Thread(target=self.handle_client, args=(self.client_socket, address))
        t5.start()


    def startCommunication(self):
        # vid send
        self.camera_client = CameraClient(self.client_ip, self.vid_send_port)
        t3 = threading.Thread(target=self.camera_client.start_stream)
        t3.daemon = True
        time.sleep(0.1)  # 1초 지연
        t3.start()
        self.toggle = 1

        # audio send
        self.audio_sender = AudioSender(self.client_ip, self.aud_send_port)
        t4 = threading.Thread(target=self.audio_sender.start_stream)
        t4.daemon = True
        time.sleep(0.1)  # 1초 지연
        t4.start()

        self.text_sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_sender.connect((self.client_ip, self.text_send_port))

        self.myvideo_thread = VideoThread(self.camera_client)
        self.myvideo_thread.daemon = True
        time.sleep(0.1)
        self.myvideo_thread.start()

    def update_pixmap(self, pixmap):
        self.chatpixmap.setPixmap(pixmap)

    def updateMyImage(self, pixmap):
        self.mypixmap.setPixmap(pixmap)

    def sendMessage(self):
        message = self.lineEdit.text()  # Get text from QTextEdit
        # 현재 메시지를 보내고 입력창 비우기
        self.text_sender.send(message.encode())
        self.lineEdit.clear()  # Clear the QTextEdit


    def closeEvent(self, event):
        self.client_socket.close()


    def handle_client(self, client_socket, address):
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            self.label.setText(data.decode())

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

class VideoThread(QThread):
    frame_updated = pyqtSignal(QPixmap)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        while self.client.__running:
            frame = self.client._get_frame()
            qImg = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(qImg)
            self.frame_updated.emit(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    sys.exit(app.exec())