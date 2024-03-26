import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QIcon, QImage
from PyQt6.QtCore import Qt, QObject, pyqtSignal

import socket
import subprocess
import re
from threading import Thread
import json
import cv2
import numpy as np

SERVER_IP = '192.168.0.31'
SERVER_PORT = 15017

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
        # IP 주소와 포트 번호를 가져옴
        ip_address = self.clientip.text()
        port_number = self.clientport.text()

        # 가져온 정보를 바탕으로 소켓 통신 진행 
        if ip_address and port_number:
            try:
                # 클라이언트와 소켓 연결
                client_socket = socket.socket()
                client_socket.connect((ip_address, int(port_number)))
                
                # 소켓이 연결되면 facechat UI를 띄우고 상대방의 얼굴 비디오를 표시
                self.openFaceChatWindow(client_socket)

                # 상대방이 통신을 끊거나 내가 통신을 끊으면 socket 종료 (연결 종료)
                client_socket.close()
            except Exception as e:
                print(f"클라이언트에 연결하는 중 오류 발생: {e}")
        else:
            print("전화를 걸기 위한 IP 주소 또는 포트 번호를 찾을 수 없습니다.")

    def openFaceChatWindow(self, client_socket):
        # facechat UI 파일을 로드합니다.
        # facechat.ui 파일에서 'chatpixmap' 웹캠 비디오를 표시하는 데 사용
        facechat_window = uic.loadUi("/home/kkyu/amr_ws/DL/project_deep/face_communication/pyqt_socket/facechat.ui")

        cap = cv2.VideoCapture('/dev/video0')

        while True:
            # 웹캠에서 프레임을 읽습니다.
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_string = cv2.imencode('.jpg', frame)[1].tostring()
            size = len(frame_string)
            client_socket.sendall(str(size).ljust(16).encode())
            client_socket.sendall(frame_string)
            length = int(client_socket.recv(16).strip())
            frame_string = recvall(client_socket, length)
            frame_array = np.frombuffer(frame_string, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.IMREAD_COLOR)

            # QLabel에 QPixmap을 표시
            facechat_window.chatpixmap.setPixmap(QPixmap.fromImage(QImage(frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)))

            # facechat 창의 제목을 설정하고 창을 표시합니다.
            facechat_window.setWindowTitle("Face Chat")
            facechat_window.show()

            # 이벤트를 확인하고 창을 업데이트합니다.
            QApplication.processEvents()

            # # 소켓이 닫히면 루프를 종료합니다.
            # if client_socket.fileno() == -1:
            #     break
            if cv2.waitKey(1) & 0xFF == 27:
                break

        # 카메라를 해제하고 창을 닫습니다.
        cap.release()
        facechat_window.close()



def recvall(sock, count):
    buf = b''

    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    sys.exit(app.exec())

