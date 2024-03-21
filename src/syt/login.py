import sys
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.uic import loadUi
import socket
import subprocess
import re
from threading import Thread
import time


SERVET_IP = '192.168.0.15'
SERVER_PORT = 15019


# 터미널에서 ifconfig 명령어 실행시켜 ip주소를 가지고 오는 함수.
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


# login ui
from_class_login = uic.loadUiType("/home/addinedu/dev_ws/DLProject/mar21/login.ui")[0]

class LoginUI(QMainWindow, from_class_login) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("login!")
        # ip주소 표시
        self.hostIP = get_ip_address("wlo1")
        self.labelIP.setText(str(self.hostIP))

        # 이벤트 설정 
        self.loginBtn.clicked.connect(self.connectServer)

        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        

    # data 보내는 함수
    def connectServer(self):
        self.userName = self.nameEdit.text()

        if self.userName:
            # 메시지 생성
            message = f"{self.userName}"

            # 문자열을 바이트로 변환하여 전송
            self.sock.connect((SERVET_IP, SERVER_PORT))
            self.sock.sendall(message.encode())
            # self.sock.close()

            # load Ui file
            self.clientUI = CientUI(self.userName, self.sock)
            self.clientUI.show()
            

# client ui 
from_class_client = uic.loadUiType("/home/addinedu/dev_ws/DLProject/mar21/client.ui")[0]

class CientUI(QDialog, from_class_client):
    def __init__(self, userName, sock):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("client!")
        
        # ui표시
        self.userNameLabel.setText(userName)
        self.peopleNum.setText(str(self.tableWidget.rowCount()))
        self.sock = sock 

        # 테이블 설정 
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(['username','connect'])
        self.addRow("Row 1")
        self.addRow("Row 2")
        self.addRow("Row 3")

        # 쓰레드 설정
        self.clientThread = Thread(target=self.AcceptServer)
        self.clientThread.start()


    def addRow(self, name):
        rowPosition = self.tableWidget.rowCount()
        self.tableWidget.insertRow(rowPosition)

        nameItem = QTableWidgetItem(name)
        self.tableWidget.setItem(rowPosition, 0, nameItem)

        button = QPushButton("Click Me")
        button.clicked.connect(lambda checked, row=rowPosition: self.buttonClicked(row))
        self.tableWidget.setCellWidget(rowPosition, 1, button)


    def buttonClicked(self, row):
        item = self.tableWidget.item(row, 0)
        if item:
            print("Button clicked in row:", row, "Name:", item.text())


    def AcceptServer(self):
        while True:
            data = self.sock.recv(1024).decode("utf-8")

            if data:
                print(data)

    def closeEvent(self, event):
        # 다이얼로그가 닫힐 때 클라이언트 스레드 종료
        self.clientThread.running = False
        self.clientThread.join()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    sys.exit(app.exec())
