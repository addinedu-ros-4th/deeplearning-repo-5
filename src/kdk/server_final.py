import sys
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem, QHeaderView, QPushButton
from PyQt6.QtCore import Qt
from PyQt6 import uic
from PyQt6.QtGui import QIcon
import socket
from threading import Thread
from datetime import datetime 
import json 


class ClientThread(Thread):
    def __init__(self, client_socket, server_instance):
        super().__init__()
        self.client_socket = client_socket
        self.server_instance = server_instance

    def run(self):
        while True:
            data = self.client_socket.recv(1024).decode()
            if not data:
                break

    def send_data(self, data):
        self.client_socket.sendall(data.encode())


class WindowClass(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("/home/kkyu/amr_ws/DL/project_deep/deeplearning-repo-5/src/kdk/server_final.ui", self)
        
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

        self.setWindowTitle("관리자 Mode")

        self.lineEdit.setText("127.0.1.1")        
        self.lineEdit2.setText("15004")

        self.btnOpen.clicked.connect(self.StartServer)
        self.btnClose.clicked.connect(self.StopServer)
        self.btnSend.clicked.connect(self.SendData)

        self.server_socket = None
        self.client_threads = []

    def get_ip_address():
        hostname = socket.gethostname()    
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    print(get_ip_address())

    def StartServer(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.1.1', 15004))  # Adjust IP address and port
        self.server_socket.listen(5)

        self.label.setText("Server Started")
        self.lineEdit.setEnabled(True)

        # Start listening for incoming connections in a separate thread
        server_thread = Thread(target=self.AcceptClients)
        server_thread.start()

        # Set client state to "ON" in the tableWidget and change color to blue
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.item(row, 3).setText("ON")
            self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.blue)

    def AcceptClients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            
            # Extract IP address and port from the client_address tuple
            ip_address = client_address[0]
            port = client_address[1]
            
            # Receive data from the client (username)
            username = client_socket.recv(1024).decode("utf-8")
            
            # Add client information to the tableWidget
            self.AddClientToTable(ip_address, port, username, state="ON")
            
            # Create an instance of ClientThread to handle each client separately
            client_thread = ClientThread(client_socket, self)
            client_thread.start()
            self.client_threads.append(client_thread)


    def HandleClient(self, client_socket):
        # Extract client IP address and port
        client_address = client_socket.getpeername()
        ip_address = client_address[0]
        port = client_address[1]

        # Receive data from the client (username)
        username = client_socket.recv(1024).decode("utf-8")
        self.AddClientToTable(ip_address, port, username, state="ON")

        client_thread = ClientThread(client_socket, self)
        client_thread.start()
        self.client_threads.append(client_thread)

        while True:
            # Receive data from the client
            data = client_socket.recv(1024).decode("utf-8")

            if not data:
                break
            # Process received data if necessary

        # Close client socket
        client_socket.close()
        # Update client state to "OFF" in the tableWidget
        self.UpdateClientState(ip_address, port, state="OFF")


    def AddClientToTable(self, ip_address, port, username, state="ON"):
        connect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 접속 시간 기록

        for row in range(self.tableWidget.rowCount()):
            if (self.tableWidget.item(row, 0).text() == ip_address and
                    self.tableWidget.item(row, 1).text() == str(port)):
                if state == "OFF":
                    self.tableWidget.item(row, 3).setText(state)
                    self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.red)
                return
        
        row = self.tableWidget.rowCount()

        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(ip_address))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(str(port))) 
        self.tableWidget.setItem(row, 2, QTableWidgetItem(username))
        self.tableWidget.setItem(row, 3, QTableWidgetItem(state))
        self.tableWidget.setItem(row, 4, QTableWidgetItem(connect_time))  # 접속 시간 표시

        if state == "OFF":
            self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.red)
        else:
            self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.blue)


    def UpdateClientState(self, ip_address, port, state):

        for row in range(self.tableWidget.rowCount()):

            if (self.tableWidget.item(row, 0).text() == ip_address and
                    self.tableWidget.item(row, 1).text() == str(port)):
                self.tableWidget.item(row, 3).setText(state)

                if state == "OFF":
                    self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.red)
                else:
                    self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.blue)
                break


    def StopServer(self):
        if self.server_socket:
            self.server_socket.close()

        self.label.setText("Server Stopped")

        self.lineEdit.setEnabled(False)
        self.btnAdd.setEnabled(False)

        # Set all client states to "OFF" in the tableWidget
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.item(row, 3).setText("OFF")
            self.tableWidget.item(row, 3).setForeground(Qt.GlobalColor.red)

        # Join all client threads
        for thread in self.client_threads:
            thread.join()

        self.client_threads = []


    def SendData(self):
        # Filter table data for rows where State is "ON" and send it to the client
        data = []
        for row in range(self.tableWidget.rowCount()):
            state_item = self.tableWidget.item(row, 3)
            if state_item and state_item.text() == "ON":
                row_data = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    if item:
                        row_data.append(item.text())
                data.append(row_data)
        
        data_dict = {"items": data}
        json_data = json.dumps(data_dict)
        
        for thread in self.client_threads:
            thread.send_data(json_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)  
    myWindows = WindowClass()     
    myWindows.show()              
    sys.exit(app.exec())
