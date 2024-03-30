import sys
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem, QHeaderView, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal,  QTimer
import socket
from threading import Thread
from datetime import datetime 
import json
import select
import time
import csv 
import mysql.connector
import os 

# 서버 ip/port 설정
SERVER_IP = "192.168.0.29"
SERVER_PORT = 15041

current_dir = os.path.dirname(os.path.abspath(__file__))

class WindowClass(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(current_dir, "server.ui"), self)
        self.setWindowTitle("Welcome to Server")
        self.setFixedSize(880,675)
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
        self.btnClose.clicked.connect(self.StopServer)
        self.btnExport.clicked.connect(self.ExportTable)
        self.tableWidget.itemChanged.connect(self.updateDatabase)
        self.tableWidget.itemChanged.connect(self.SendTableUpdateToClients)

        self.infolabel = QLabel('༼๑◕ ◞◟ ◕๑༽ 서버에 오신 것을 환영합니다 ༼๑◕ ◞◟ ◕๑༽', self)
        self.infolabel.setStyleSheet('font-size: 18pt; font-weight: bold;')
        self.infolabel.adjustSize()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.moveLabel)
        self.timer.start(10)  # 10 milliseconds
        
        self.posX = self.width()

        # MySQL 연결 정보
        self.db_config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '7500',
            'database': 'HyunZZoom'  
        }

    def moveLabel(self):
        self.infolabel.move(self.posX, 0)
        self.posX -= 1
        if self.posX + self.infolabel.width() < 0:
            self.posX = self.width()

    def StartServer(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(5)             
        self.lineEdit.setEnabled(True)

        self.infolabel.setText('٩( ͡◉ ̯ ͡◉)۶ 서버가 활성화되었습니다!!!! ٩( ͡◉ ̯ ͡◉)۶')

        # Start listening for incoming connections in a separate thread
        server_thread = Thread(target=self.AcceptClients)
        server_thread.start()


    def StopServer(self):
        # Close the server socket
        if hasattr(self, 'server_socket') and self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"Error while closing server socket: {e}")
        
        # Disable the lineEdit and update the info label
        self.lineEdit.setEnabled(False)
        self.infolabel.setText('¯\_(ツ)_/¯ 서버가 비활성화되었습니다. ¯\_(ツ)_/¯')

    def ExportTable(self):
        # Generate file name with today's date
        today_date = datetime.now().strftime("%Y-%m-%d")
        file_name = f"Client_information_{today_date}.csv"

        file_path, _ = QFileDialog.getSaveFileName(self, 'Save CSV File', file_name, 'CSV Files (*.csv)')
        if file_path:
            headers = ["Connect Time", "IP", "Port", "Username", "State"]
            with open(file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(headers)
                for row in range(self.tableWidget.rowCount()):
                    row_data = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append("")  
                    csv_writer.writerow(row_data)


    def updateDatabase(self, item):
        try:
            # MySQL 데이터베이스 연결
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # 현재 시간을 가져와서 형식화
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 변경된 셀의 정보 가져오기
            row = item.row()
            ip = self.tableWidget.item(row, 1).text()
            port = int(self.tableWidget.item(row, 2).text())
            username = self.tableWidget.item(row, 3).text()
            state = self.tableWidget.item(row, 4).text()

            # 데이터베이스에 삽입할 시간 표시
            current_db_time = current_time

            # 이전 접속 시간 가져오기
            cursor.execute('SELECT connect_time FROM Client_info WHERE ip = %s AND port = %s AND username = %s', (ip, port, username))
            previous_connect_time = cursor.fetchone()

            # 만약 이전 접속 시간이 존재하고, 현재 시간과 같다면 '-'로 표시
            if previous_connect_time and previous_connect_time[0] == current_db_time:
                current_db_time = '-'  # 동일한 시간이면 특별한 표시

            # 변경된 셀의 정보를 데이터베이스에 삽입
            cursor.execute('INSERT INTO Client_info (connect_time, ip, port, username, state) VALUES (%s, %s, %s, %s, %s)',
                        (current_db_time, ip, port, username, state))

            conn.commit()
            conn.close()

        except mysql.connector.Error as err:
            print(f"MySQL 오류: {err}")



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
                    self.infolabel.setText(f"{username}님이 입장하셨습니다 (ू˃o˂ू)")
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
                        self.infolabel.setText(f"{self.tableWidget.item(row, 3).text()}님이 연결 중입니다.")

                        return
                    
            elif table_toggle == 2:
                for row in range(self.tableWidget.rowCount()):
                    if self.tableWidget.item(row, 2).text() == message:
                        name = self.tableWidget.item(row, 3).text()

                for row in range(self.tableWidget.rowCount()):
                    if (self.tableWidget.item(row, 1).text() == ip and
                        self.tableWidget.item(row, 2).text() == str(port)):
                            self.tableWidget.setItem(row, 4, QTableWidgetItem(f"[{name}] Connected"))
                            self.infolabel.setText(f"{name}님이 연결되었습니다.")

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
