import sys
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem, QHeaderView, QPushButton
from PyQt6.QtCore import Qt
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
import socket
from threading import Thread
from datetime import datetime 
import json
import select
import time

# 서버 ip/port 설정
SERVER_IP = "192.168.0.33"
SERVER_PORT = 15035
path = "/home/rds/Desktop/git_ws/deeplearning-repo-5/src/ljh/socket_final/"
class WindowClass(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(path + "server.ui", self)
        self.setWindowTitle("관리자 Mode")
        self.lineEdit.setText(SERVER_IP)        
        self.lineEdit2.setText(str(SERVER_PORT))

        # 클라이언트 정보를 저장할 딕셔너리 설정 
        self.clients_info = {}

        # 테이블 설정 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget.setStyleSheet("QTableWidget { background-color: #f0f0f0; }"
                                        "QTableWidget QTableWidget:item { color: #333333; }"
                                        "QTableWidget::item:selected { background-color: #b8daff; }"
                                        "QHeaderView::section { background-color: #007bff; color: white; }"
                                        "QTableWidget::item { padding: 5px; }")
        for button in self.findChildren(QPushButton):
            if button.objectName() == "btnAdd":
                button.setStyleSheet("background-color: #CCCCCC; color: black; font-weight: bold;")
            elif button.objectName() == "btnOpen":
                button.setStyleSheet("background-color: #B3D9FF; color: black; font-weight: bold;")
            elif button.objectName() == "btnClose":
                button.setStyleSheet("background-color: #FF6666; color: black; font-weight: bold;")

        
        # 이벤트 설정 
        self.btnOpen.clicked.connect(self.StartServer)
        self.tableWidget.itemChanged.connect(self.SendTableUpdateToClients)



    def StartServer(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(5)             
        self.label.setText("Server Started")
        self.lineEdit.setEnabled(True)

        # Start listening for incoming connections in a separate thread
        server_thread = Thread(target=self.AcceptClients)
        server_thread.start()



    def AcceptClients(self):
        while True:
            read_sockets, _, _ = select.select([self.server_socket] + list(self.clients_info.keys()), [], [])
            for sock in read_sockets:
                if sock == self.server_socket:
                    # 새로운 클라이언트가 연결 요청을 보냄
                    client_socket, client_address = self.server_socket.accept()
                    ip = client_address[0]
                    port = client_address[1]
                    username = client_socket.recv(1024).decode("utf-8")
                    # 클라이언트 정보를 딕셔너리에 추가
                    self.clients_info[client_socket] = [ip, port, username, "ON", datetime.now()]
                    # print(self.clients_info)
                    # 테이블에 클라이언트 정보 추가
                    self.AddClientToTable(ip, port, username, state='ON')
                else:
                    # 클라이언트로부터 데이터 수신
                    data = sock.recv(1024)
                    if data:
                        string_data = data.decode('utf-8')
                        ip, port = sock.getpeername()
                        id = string_data.split('|')[0]
                        message = string_data.split('|')[1]

                        if id == 'Connecting':
                            print(message)
                            print(ip, port)
                            table_toggle = 1
                            self.ModifyClientFromTable(table_toggle, ip, port, message)
                            
                        elif id == 'Connected':
                            print(message)
                            print(ip, port)
                            table_toggle = 2
                            self.ModifyClientFromTable(table_toggle, ip, port, message)

                        else:
                            pass
                    
                    else:
                        # 클라이언트 연결 종료
                        sock.close()
                        client_info = self.clients_info.pop(sock)
                        self.RemoveClientFromTable(client_info[0], client_info[1])


    def AddClientToTable(self, ip, port, username, state="ON"):
        connect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 접속 시간 기록
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(connect_time))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(ip))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(str(port))) 
        self.tableWidget.setItem(row, 3, QTableWidgetItem(username))
        self.tableWidget.setItem(row, 4, QTableWidgetItem(state))  # 접속 시간 표시



    def RemoveClientFromTable(self, ip, port):
        for row in range(self.tableWidget.rowCount()):
            if (self.tableWidget.item(row, 1).text() == ip and
                self.tableWidget.item(row, 2).text() == str(port)):
                self.tableWidget.removeRow(row)
                self.SendTableUpdateToClients()
                return
            

    def ModifyClientFromTable(self, table_toggle, ip, port, message):
            if table_toggle == 1:
                for row in range(self.tableWidget.rowCount()):
                    if (self.tableWidget.item(row, 1).text() == ip and
                        self.tableWidget.item(row, 2).text() == str(port)):
                        self.tableWidget.setItem(row, 4, QTableWidgetItem(f"[{message}] Connecting"))
                        return
                    
            elif table_toggle == 2:
                for row in range(self.tableWidget.rowCount()):
                    if self.tableWidget.item(row, 2).text() == message:
                        name = self.tableWidget.item(row, 3).text()

                for row in range(self.tableWidget.rowCount()):
                    if (self.tableWidget.item(row, 1).text() == ip and
                        self.tableWidget.item(row, 2).text() == str(port)):
                            self.tableWidget.setItem(row, 4, QTableWidgetItem(f"[{name}] Connected"))
                return


                
    def SendTableUpdateToClients(self):
        time.sleep(0.2)
        data = []
        for row in range(self.tableWidget.rowCount()):
            state_item = self.tableWidget.item(row, 4)
            
            if state_item and (state_item.text() == "ON" 
                or "Connecting" in state_item.text()
                or "Connected" in state_item.text()):

                row_data = []

                for column in range(1, self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    if item:
                        row_data.append(item.text())
                data.append(row_data)
        
        data_dict = {"items": data}
        json_data = json.dumps(data_dict)
        
        for client_socket in self.clients_info.keys():
            client_socket.sendall(json_data.encode())


       
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec())
