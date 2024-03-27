import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QIcon, QImage, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal

import socket
import subprocess
import re
from threading import Thread
import json
import cv2
import numpy as np

import pyaudio
import threading

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
from_class_login = uic.loadUiType("/home/kkyu/amr_ws/DL/project_deep/face_communication/pyqt_socket/login_final.ui")[0]

class LoginUI(QMainWindow, from_class_login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("WELCOME")
        # ip주소 표시
        self.hostIP = get_ip_address("wlo1")
        self.labelIP.setText(str(self.hostIP))

        self.setWindowIcon(QIcon('/home/kkyu/amr_ws/DL/project_deep/face_communication/data_pic/addinedu.png'))

        pixmap = QPixmap('/home/kkyu/amr_ws/DL/project_deep/face_communication/data_pic/background.jpg')
        self.labelpixmap.setPixmap(pixmap)

        pixmap2 = QPixmap('/home/kkyu/amr_ws/DL/project_deep/face_communication/data_pic/client.png')
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
from_class_client = uic.loadUiType("/home/kkyu/amr_ws/DL/project_deep/face_communication/pyqt_socket/client_final.ui")[0]

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

        
        self.callButton.clicked.connect(self.callButtonClicked)

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
                
                # 버튼 생성 및 삽입
                button = QPushButton("Connect")
                button.setObjectName("connectButton")  # Set object name for styling
                button.clicked.connect(lambda _, row=row: self.connectButtonClicked(row))
                self.tableWidget.setCellWidget(row, len(item), button)
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


    def callButtonClicked(self):
            ip_address = self.clientip.text()
            port_number = self.clientport.text()

            if ip_address and port_number:
                try:
                    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_socket.bind((ip_address, int(port_number)))
                    server_socket.listen(True) 
                    QMessageBox.information(self, "Connection", "Waiting for connection...")

                    while True:
                        client_socket, addr = server_socket.accept()
                        QMessageBox.information(self, "Connection", f"Connected with {addr}")

                        threading.Thread(target=self.openFaceChatWindow, args=(client_socket,)).start()

                except Exception as e:
                    print(f"Error while connecting to clients: {e}")
            else:
                print("IP address or port number not found.")

    def openFaceChatWindow(self, client_socket):
        self.facechat_window = FaceChatWindow(client_socket)
        self.facechat_window.show()
        # speakButton을 찾아 연결
        self.facechat_window.gestureButton_2 = self.facechat_window.findChild(QPushButton, "speakButton")
        self.facechat_window.gestureButton_2.clicked.connect(self.facechat_window.handleSpeakButton)
            


class FaceChatWindow(QDialog):
    def __init__(self, client_socket):
        super().__init__()
        uic.loadUi("/home/addinedu/dev_ws/deeplearning-repo-5/src/kdk/facechat.ui", self)
        self.client_socket = client_socket

        self.frame_thread = Thread(target=self.send_frames)
        self.frame_thread.daemon = True
        self.frame_thread.start()


    def send_frames(self):

        cap = cv2.VideoCapture('/dev/video0')

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_string = cv2.imencode('.jpg', frame)[1].tostring()
            size = len(frame_string)
            self.client_socket.sendall(str(size).ljust(16).encode())
            self.client_socket.sendall(frame_string)
            length = int(self.client_socket.recv(16).strip())
            print("Receiving frame of size:", length)
            frame_string = recvall(self.client_socket, length)
            frame_array = np.frombuffer(frame_string, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      

            self.chatpixmap.setPixmap(QPixmap.fromImage(QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888)))

            # facechat 창의 제목을 설정하고 창을 표시합니다.
            self.setWindowTitle("Face Chat")
            self.show()

            # 이벤트를 확인하고 창을 업데이트합니다.
            QApplication.processEvents()

            # # 소켓이 닫히면 루프를 종료합니다.
            if cv2.waitKey(1) & 0xFF == 27:
                break
        cap.release()
                                 

    def handleSpeakButton(self, client_socket):
        # 오디오 송수신을 담당하는 함수와 스레드를 시작합니다.
        audio_thread = threading.Thread(target=self.start_audio_communication, args=(client_socket,))
        audio_thread.daemon = True
        audio_thread.start()


    def start_audio_communication(self, client_socket):
        # PyAudio 설정
        audio = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024

        # 오디오 스트림 열기
        input_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        output_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        # 오디오 수신 및 재생을 위한 함수
        def receive_and_play():
            try:
                while True:
                    # 클라이언트로부터 오디오 데이터 수신
                    data = client_socket.recv(CHUNK)
                    if not data:
                        break
                    # 오디오 데이터 재생
                    output_stream.write(data)
            except KeyboardInterrupt:
                pass

        # 오디오 수신 및 재생을 위한 스레드 시작
        receive_thread = threading.Thread(target=receive_and_play)
        receive_thread.start()

        try:
            while True:
                # 내 마이크에서 오디오 데이터 읽기
                data = input_stream.read(CHUNK)
                # 클라이언트로 오디오 데이터 보내기
                client_socket.sendall(data)
        except KeyboardInterrupt:
            pass
        finally:
            # 연결 종료
            client_socket.close()
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()
            audio.terminate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    sys.exit(app.exec())