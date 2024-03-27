from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QIcon, QImage
from PyQt6.QtCore import Qt, pyqtSignal, QThread

import socket
import subprocess
import re
from threading import Thread
import json
import cv2
import numpy as np
import pyaudio
import sys

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
        self.tableWidget.setStyleSheet("""
            QTableWidget { background-color: #f0f0f0; }
            QTableWidget QTableWidget::item { color: #333333; }
            QTableWidget QTableWidget::item:selected { background-color: #b8daff; }
            QTableWidget QHeaderView::section { background-color: #007bff; color: white; }
            QTableWidget QTableWidget::item { padding: 5px; }
        """)

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
        port_number = self.clientport.text()
        self.facechat_window = FaceChatWindow(ip_address, int(port_number))
        self.facechat_window.show()


class VideoThread(QThread):
    change_server_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, ip_address, port_number):
        super().__init__()
        self.ip_address = ip_address
        self.port_number = port_number
    

    def run(self):

        self.sock = socket.socket()
        self.sock.connect((self.ip_address, int(self.port_number)))

        cap = cv2.VideoCapture('/dev/video0')

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_string = cv2.imencode('.jpg', frame)[1].tostring()
            size = len(frame_string)
            self.sock.sendall(str(size).ljust(16).encode())
            self.sock.sendall(frame_string)
            length = int(self.sock.recv(16).strip())
            frame_string = recvall(self.sock, length)
            frame_array = np.frombuffer(frame_string, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            self.change_server_pixmap_signal.emit(frame)  # Emit the frame to update server webcam label
            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.sock.close()
        cv2.destroyAllWindows()

class FaceChatWindow(QDialog):
    def __init__(self, ip_address, port_number):
        super().__init__()
        uic.loadUi("/home/kkyu/amr_ws/DL/project_deep/face_communication/pyqt_socket/facechat.ui", self)

        self.video_thread = VideoThread(ip_address, int(port_number))     
        self.video_thread.change_server_pixmap_signal.connect(self.update_server_image)
        self.video_thread.start()

    def update_server_image(self, frame):
        """Updates the image shown in the server webcam label."""
        qt_img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)
        self.chatpixmap.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    sys.exit(app.exec())

