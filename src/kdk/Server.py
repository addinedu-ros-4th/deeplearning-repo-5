import sys
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem, QHeaderView, QSizePolicy
from PyQt6 import uic

# Import socket module for server implementation
import socket

class WindowClass(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("/home/kkyu/amr_ws/DL/project_deep/face_communication/Server.ui", self)
        
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.lineEdit.setText("192.168.0.15")        
        self.lineEdit2.setText("65432")

        self.btnAdd.clicked.connect(self.Add)
        self.btnOpen.clicked.connect(self.StartServer)
        self.btnClose.clicked.connect(self.StopServer)

        # Initialize server socket
        self.server_socket = None

    def Add(self):
        ip_address = self.lineEdit.text()
        host_name = "KDK"  # You need to specify how to get host name
        state = "ON"  # You need to specify how to get state
        
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(ip_address))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(host_name))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(state))

    def StartServer(self):
        # Start the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('192.168.0.15', 12345))  # Adjust IP address and port
        self.server_socket.listen(5)

        # Update label
        self.label.setText("Server Started")

        # Enable client interaction
        self.lineEdit.setEnabled(True)
        self.btnAdd.setEnabled(True)

        # Find the row with the server's IP address and update the state to "ON"
        for row in range(self.tableWidget.rowCount()):
            ip_item = self.tableWidget.item(row, 0)
            if ip_item and ip_item.text() == "192.168.0.15":  # Adjust the IP address
                state_item = self.tableWidget.item(row, 2)
                if state_item:
                    state_item.setText("ON")
                break

    def StopServer(self):
        # Close the server socket
        if self.server_socket:
            self.server_socket.close()

        # Update label
        self.label.setText("Server Stopped")

        # Disable client interaction
        self.lineEdit.setEnabled(False)
        self.btnAdd.setEnabled(False)

        # Find the row with the server's IP address and update the state to "OFF"
        for row in range(self.tableWidget.rowCount()):
            ip_item = self.tableWidget.item(row, 0)
            if ip_item and ip_item.text() == "192.168.0.15":  # Adjust the IP address
                state_item = self.tableWidget.item(row, 2)
                if state_item:
                    state_item.setText("OFF")
                break

if __name__ == "__main__":
    app = QApplication(sys.argv)  
    myWindows = WindowClass()     
    myWindows.show()              
    sys.exit(app.exec())


