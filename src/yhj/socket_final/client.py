import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QIcon, QImage, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread, QTimer
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
from jamo import j2hcj, h2j
from jamos import cons, vowels, cons_double, double_cons, gesture2text
from playsound import playsound
import asyncio
import qasync
from trie import Trie
from mediapipe_thread import *
from speech_recognition_thread import *
from gtts import gTTS
import pandas as pd
import os 

SERVER_IP = '192.168.0.18'
SERVER_PORT = 15032


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

        self.setWindowIcon(QIcon('data/addinedu.png'))

        pixmap = QPixmap('data/background.jpg')
        self.labelpixmap.setPixmap(pixmap)

        pixmap2 = QPixmap('data/client.png')
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
        _, self.myport= sock.getsockname()

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
        ip_address_item = self.tableWidget.item(row, 0)
        port_item = self.tableWidget.item(row, 1)
        host_name_item = self.tableWidget.item(row, 2)
        state_item = self.tableWidget.item(row, 3)

        if all(item is not None for item in [ip_address_item, port_item, host_name_item, state_item]):
            ip_address = ip_address_item.text()
            port_number = port_item.text()
            host_name = host_name_item.text()
            state = state_item.text()

            # Construct string data
            string_data = f"Connecting|{host_name}"

            try:
                # Send string data to the server
                self.sock.send(string_data.encode())
                # Update the client IP and port labels
                self.clientip.setText(ip_address)
                self.clientport.setText(port_number)
            except Exception as e:
                print(f"Error sending data to server: {e}")
        else:
            print("Some information is missing for this row.")


    def openFaceChatWindow(self):

        ip_address = self.clientip.text()
        port_number = int(self.clientport.text())

        string_data = f"Connected|{port_number}"

        self.sock.send(string_data.encode())

        self.facechat_window = FaceChatWindow(ip_address, port_number, self.myport)
        self.facechat_window.show()

class FaceChatWindow(QDialog):
    def __init__(self, ip_address,port_number, my_port):
        super().__init__()
        uic.loadUi("drl_demo.ui", self)
        # Port number configuration
        self.hostIP = get_ip_address("wlo1")
        self.local_ip_address = self.hostIP
        self.client_ip = ip_address
        self.vid_recv_port = port_number + 1
        self.vid_send_port = my_port + 1
        self.aud_recv_port = port_number + 2
        self.aud_send_port = my_port + 2
        self.text_recv_port = port_number + 3
        self.text_send_port = my_port + 3
       

        self.camera_client = CameraClient(self.client_ip, self.vid_send_port, x_res=540, y_res=540)
        self.camera_thread = CameraThread(self.camera_client)        
        self.gestureButton.clicked.connect(self.startCommunication)

        # vid recv (서버 설정)
        self.stream_recv = StreamingServerModified(self.local_ip_address, self.vid_recv_port)
        self.stream_recv.frame_updated.connect(self.update_pixmap)
        self.stream_recv_thread = QThread()
        self.stream_recv.moveToThread(self.stream_recv_thread)
        self.stream_recv_thread.started.connect(self.stream_recv.start_server)
        self.stream_recv_thread.start()

        # audio recv (서버설정)
        audio_recv = AudioReceiver(self.local_ip_address, self.aud_recv_port)   
        t2 = threading.Thread(target=audio_recv.start_server)
        t2.daemon = True
        time.sleep(0.1) 
        t2.start()

        # text recv (서버설정)
        self.text_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_recv.bind((self.local_ip_address, self.text_recv_port))
        self.text_recv.listen(True)

        t_accept = threading.Thread(target=self.accept_client)
        t_accept.daemon = True
        t_accept.start()
                
        
        self.speech_recognition_thread = SpeechRecognitionThread()
        self.speech_recognition_thread.recognition_result.connect(self.on_recognition_result)
        self.mediapipe_thread = MediapipeThread('handModel.h5')
        self.mediapipe_thread.update_word_signal.connect(self.update_word_label)
        
        
        self.csv_path = "autocorrect.csv"           #ip, id 별로 DB 저장
        self.last_word_time = 0
        self.autoword_1.setVisible(False)
        self.autoword_2.setVisible(False)
        self.autoword_3.setVisible(False)
        self.autoword_4.setVisible(False)
        self.autoword_5.setVisible(False)
        self.record_btn.setVisible(False)
        self.cache = self.load_csv()
        self.text = ""
        self.sub = []
        self.prefix = ""
        self.file_name = "text_to_speech.mp3"
        self.trie = Trie()
        self.cons = cons
        self.vowels = vowels
        self.cons_double = cons_double
        self.flag = 0
        self.mt = ""
        self.setWindowTitle("Autocorrect")
        self.input.textChanged.connect(self.on_text_changed)
        self.last_hand_time = 0
        
        # QTimer 객체 생성
        self.timer = QTimer(self)
        # QTimer 이벤트와 연결할 함수 설정
        self.timer.timeout.connect(self.update_word)
        # 0.5초마다 타이머를 시작
        self.timer.start(1)  # 500ms = 0.5초
        
        self.autoword_1.clicked.connect(self.changeText_1)
        self.autoword_2.clicked.connect(self.changeText_2)
        self.autoword_3.clicked.connect(self.changeText_3)
        self.autoword_4.clicked.connect(self.changeText_4)
        self.autoword_5.clicked.connect(self.changeText_5)
        self.btn_reset.clicked.connect(self.reset_line)
        self.word_list = []
        self.speed = 8
        self.HTT.toggled.connect(self.on_radio_toggled)
        self.STT.toggled.connect(self.on_radio_toggled)
        
        # self.sub_label.textChanged.connect(self.change_text)
        
        self.sub_timer = QTimer()
        # self.sub_timer.setInterval(3000)  # 3초마다 타이머 시그널 발생
        self.sub_timer.setSingleShot(True)
        self.sub_timer.timeout.connect(self.reset_sub)  # 타임아웃 시그널에 연결할 함수 설정
    

        self.record_btn.clicked.connect(self.toggleRecording)

        self.hand_speed.setMinimum(1)
        self.hand_speed.setMaximum(15)
        self.hand_speed.setValue(self.speed)
        self.hand_speed.setTickInterval(1)
        self.hand_speed.valueChanged.connect(self.sliderValueChanged)
        self.speed_label.setText(str(self.speed)) 

        # self.show()
      

    def sliderValueChanged(self, value):
        # 슬라이더 값(value)을 self.speed에 반영
        self.speed = 16-value
        self.speed_label.setText(str(value)) 

    def toggleRecording(self):
        if self.record_btn.text() == "Start Speech":
            self.record_btn.setText("Stop Speech")
            self.speech_recognition_thread.start()
            time.sleep(0.1)
            self.HTT.setEnabled(False)  # HTT 라디오 버튼 비활성화
        else:
            self.record_btn.setText("Start Speech")
            self.speech_recognition_thread.stop()
            time.sleep(1)
            self.HTT.setEnabled(True)  # HTT 라디오 버튼 비활성화

            
    def load_csv(self):
        try:
            return pd.read_csv(self.csv_path)
        except FileNotFoundError:
            return pd.DataFrame(columns=['word', 'frequency'])


    def on_radio_toggled(self):
        # while not camera_image_queue.empty() :
        #     camera_image_queue.get()
        if self.HTT.isChecked():
            self.STT.setChecked(False)
            time.sleep(0.1)                         #delay를 줘서 인식 속도를 맞춘다
            print("hi")

            self.record_btn.setVisible(False)
            if not self.mediapipe_thread.isRunning():  # 이미 실행 중인 경우 다시 시작하지 않음
                self.mediapipe_thread.start()
            self.speech_recognition_thread.stop()
             

        elif self.STT.isChecked():
            time.sleep(0.1)
            self.HTT.setChecked(False)
            if self.mediapipe_thread.isRunning():  # 이미 실행 중인 경우 다시 시작하지 않음
                self.mediapipe_thread.stop()
            self.record_btn.setVisible(True)

    def on_recognition_result(self, text):
        
        # self.sub.append(text)
        # sub_text = ' '.join(self.sub)
        sub_text = text + " "
        self.input.setText(sub_text)
        
        #self.sub_timer.start(3000)



    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F1:
            self.save_csv()
            # PyQt6 애플리케이션 종료
            self.close()
            
            # text_to_speech.mp3 파일 삭제
            file_path = "text_to_speech.mp3"
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            # 다른 키가 눌렸을 때의 동작
            pass
            
    
        
    def update_word(self):
        if hasattr(self, 'word') and self.word:  # 단어가 존재하고 값이 비어있지 않은 경우에만 실행
            self.word_list.append(self.word)
            self.text_label.setText(self.word)
            self.word = ""
            print(self.word_list)

            # 입력 리스트에 다섯 개의 값이 쌓였을 경우
            if len(self.word_list) >= self.speed:
                output = max(set(self.word_list), key=self.word_list.count)

                self.word_list = []
            
                if output == 'space':
                    self.text += " "
                elif output == 'backspace':
                    # 마지막 문자를 제거합니다.
                    self.text = self.text[:-1]
                    if self.text == "":
                        self.autoword_1.setVisible(False)
                        self.autoword_2.setVisible(False)
                        self.autoword_3.setVisible(False)
                        self.autoword_4.setVisible(False)
                        self.autoword_5.setVisible(False)
                elif output == "shift":
                    self.flag = 1
                    print(self.flag)

                elif output == "question":
                    self.text += "?"
                # QLineEdit에 텍스트 업데이트
                elif self.flag == 1 and output in ["ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ"]:
                    # 적절한 된소리로 변경하는 처리를 수행합니다.
                    if output == "ㄱ":
                        self.text += "ㄲ"
                    elif output == "ㄷ":
                        self.text += "ㄸ"
                    elif output == "ㅂ":
                        self.text += "ㅃ"
                    elif output == "ㅅ":
                        self.text += "ㅆ"
                    elif output == "ㅈ":
                        self.text += "ㅉ"
                    # flag를 다시 초기화합니다.
                    self.flag = 0
                else:
                    self.text += output
                    
                    # 자음이 입력되었을 때도 flag를 0으로 설정합니다.
                    if output in ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"]:
                        self.flag = 0                                                                                                
                    
                self.input.setText(self.text)  # 'word'는 QLineEdit의 objectName
        
            self.last_hand_time = time.time()
        
        elif time.time() - self.last_hand_time >= 0.3:  # self.word가 0.3초 동안 존재하지 않으면
            self.word_list = [] 
            self.text_label.setText("") 
    
    def reset_line(self):
        self.input.clear()  # Line edit의 문자열을 삭제합니다.

    def speech_word(self, word_to_speech):
        # 비동기 작업을 스케줄합니다.
        asyncio.ensure_future(self.async_speech_word(word_to_speech))

    async def async_speech_word(self, word_to_speech):
        # gTTS 작업을 별도의 스레드에서 실행합니다.
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.create_speech_file, word_to_speech)
        # playsound 작업을 별도의 스레드에서 실행합니다.
        await loop.run_in_executor(None, playsound, self.file_name)

    def create_speech_file(self, text):
        tts_ko = gTTS(text=text, lang='ko')
        tts_ko.save(self.file_name)
        
    def save_csv(self):
        self.cache.to_csv(self.csv_path, index=False)
        print("save")


    def add_word(self, input_word):
        self.sub_timer.start(3000)
        self.sub.append(input_word)
        sub_text = ' '.join(self.sub)
        self.sub_label.setText(sub_text)
        if input_word.strip():  # 입력된 단어가 공백이 아닌지 확인
            if input_word in self.cache['word'].values:
                index = self.cache.index[self.cache['word'] == input_word].tolist()
                self.cache.loc[index, 'frequency'] += 1
            else:
                self.cache.loc[len(self.cache)] = [input_word, 1]
        self.last_word_time = time.time()  # 마지막 입력 시간 갱신
    
    def reset_sub(self):
        # 마지막 입력된 단어가 없거나 마지막 입력 시간이 3초 이상 경과하면 sub 초기화
            self.sub = []
            self.sub_label.setText("")
    # def add_word(self, input_word):                 #method 분리
    #     time.sleep(0.1)
    #     if input_word.strip():  # 입력된 단어가 공백이 아닌지 확인
    #         word_df = pd.read_csv(self.csv_name)  # 여기서 CSV 파일 경로 수정
    #         if input_word in word_df['word'].values:
    #             index = word_df.index[word_df['word'] == input_word].tolist()
    #             word_df['frequency'][index] += 1
    #             print("fre")
    #         else:
    #             word_df.loc[len(word_df)] = [input_word, 1]
    #             print("word")

    #         word_df.to_csv(self.csv_name, index=False)
    
    def changeText_1(self) :
        word = self.text.split()
        new_word = self.autoword_1.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  
            
    def changeText_2(self) :
        word = self.text.split()
        new_word = self.autoword_2.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)

    def changeText_3(self) :
        word = self.text.split()
        new_word = self.autoword_3.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)

    def changeText_4(self) :
        word = self.text.split()
        new_word = self.autoword_4.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  

    def changeText_5(self) :
        word = self.text.split()
        new_word = self.autoword_5.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  
            
            
    def update_camera_screen(self, qt_img):
        # camera_screen QLabel에 이미지 표시
        self.camera_screen.setPixmap(QPixmap.fromImage(qt_img))

    def update_word_label(self, word):
        # detected_word_label QLabel에 단어 표시
        self.word = word

    def on_text_changed(self):
        self.word_df = self.cache
        self.words = self.word_df['word']
        self.text = self.input.text()
        self.text = j2hcj(h2j(self.text))
        if len(self.text) >= 2 and self.text[-2] in double_cons:  # 인덱스 접근 전에 길이 확인
            # 새로운 문자열을 생성하여 할당
            self.text = self.text[:-2] + double_cons[self.text[-2]] + self.text[-1] 
        self.text = gesture2text(self.text)
        
        for word in self.words:
            self.trie.insert(word)
            
        if self.text.strip():  # 입력이 공백이 아닌 경우에만 처리
            if self.text[-1] == " ":
                if len(self.text.split(" ")) >= 3:
                    print(self.text)
                    self.sendMessage(self.text)
                    #self.speech_word(self.text)
                    for word in self.text.split(" "):
                        self.add_word(word)
                    self.text = ""
                    self.input.setText(self.text)
                else:
                    print("Space 입력이 감지되었습니다.")
                    self.prefix = self.text.split(" ")[-2]
                    self.sendMessage(self.prefix)
                    print(self.prefix)
                    #self.speech_word(self.prefix)
                    self.add_word(self.prefix)
                    self.text = ""
                    self.input.setText(self.text)
            else:
                
                self.prefix = self.text.split(" ")[-1]                            
                self.input.setText(self.text)
                suggestions = self.trie.get_words_with_prefix(self.prefix)
                indices = [self.word_df.index[self.word_df['word'] == item].tolist() for item in suggestions]
                word_list_with_frequency = [(self.word_df.at[index[0], 'word'], self.word_df.at[index[0], 'frequency']) for index in indices]
                sorted_word_list = sorted(word_list_with_frequency, key=lambda x: x[1], reverse=True)
                suggestions = [word for word, _ in sorted_word_list]
                if suggestions:
                    if len(suggestions) > 5:
                        suggestions = suggestions[:5]
                    for i, suggestion in enumerate(suggestions, 1):
                        getattr(self, f'autoword_{i}').setText(suggestion)
                        getattr(self, f'autoword_{i}').setVisible(True)
                    for i in range(5-len(suggestions)):
                        getattr(self, f'autoword_{5-i}').setVisible(False)
                else : 
                    self.autoword_1.setVisible(False)
                    self.autoword_2.setVisible(False)
                    self.autoword_3.setVisible(False)
                    self.autoword_4.setVisible(False)
                    self.autoword_5.setVisible(False)

    
    def accept_client(self):
        self.client_socket, address = self.text_recv.accept()
        t5 = threading.Thread(target=self.handle_client, args=(self.client_socket, address))
        time.sleep(0.1)
        t5.start()


    def startCommunication(self):

        # self.camera_client = CameraClient(self.client_ip, self.vid_send_port, x_res=320, y_res=240)
        # self.toggle = 1
        # self.camera_thread = CameraThread(self.camera_client)

        #camera_client = CameraClient(self.client_ip, self.vid_send_port)
        t3 = threading.Thread(target=self.camera_client.start_stream)
        t3.daemon = True
        time.sleep(0.1)  # 1초 지연
        t3.start()
        time.sleep(0.1)
        self.camera_thread.start()
        self.camera_thread.change_pixmap_signal.connect(self.update_camera_screen)  
        # self.camera_client.start_stream()
        
        # audio send
        audio_sender = AudioSender(self.client_ip, self.aud_send_port)
        t4 = threading.Thread(target=audio_sender.start_stream)
        t4.daemon = True
        time.sleep(0.1)  # 1초 지연
        t4.start()

        self.text_sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_sender.connect((self.client_ip, self.text_send_port))

    def update_pixmap(self, pixmap):
        self.recive_screen.setPixmap(pixmap)

    def sendMessage(self, message):
        
        # 현재 메시지를 보내고 입력창 비우기
        self.text_sender.send(message.encode())
        #self.lineEdit.clear()  # Clear the QTextEdit


    def closeEvent(self, event):
        self.client_socket.close()


    def handle_client(self, client_socket, address):
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            # 받은 데이터를 처리하거나 다른 클라이언트에게 전달하는 등의 작업 수행
            self.sub_label_2.setText(data.decode())


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myLogin = LoginUI()
    myLogin.show()
    # #sys.exit(app.exec())
    # widget = FaceChatWindow()
    # widget.show()

    loop = qasync.QEventLoop(app)           #종료 권한 관리

    loop.run_forever() 