from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QLineEdit,QDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import sys
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import mediapipe as mp
from PyQt6 import uic
from hangul_utils import join_jamos
from jamos import gesture2text, cons, vowels, cons_double, double_cons
import pandas as pd
from jamo import h2j, j2hcj
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr
from trie import Trie
import time


data_dict = {0 : "ㄱ", 1 : "ㄴ", 2 : "ㅋ", 3 : "ㅌ", 4 : "ㅍ", 
             5 : "ㅎ", 6 : "ㅏ", 7 : "ㅑ", 8 : "ㅓ", 9 : "ㅕ",
             10 : "ㅗ", 11 : "ㅛ", 12 : "ㄷ", 13 : "ㅜ", 14 : "ㅠ",
             15 : "ㅡ", 16 : "ㅣ", 17 : "ㅐ", 18 : "ㅔ", 19 : "ㅚ",
             20 : "ㅟ", 21 : "ㅒ", 22 : "ㅖ", 23 : "ㄹ", 24 : "ㅢ",
             25 : "ㅁ", 26 : "ㅂ", 27 : "ㅅ", 28 : "ㅇ", 29 : "ㅈ",
             30 : "ㅊ", 31 : "backspace", 32 : "question", 33 : "shift", 34 : "space"}

# 카메라 처리를 위한 별도의 스레드 클래스
class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    update_word_signal = pyqtSignal(str)

    def run(self):
        cap = cv2.VideoCapture(0)
        
        model = load_model('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/handModel.h5')  # 모델 경로 설정

        with mp.solutions.hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7) as hands:
            with mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5) as pose:
                while True:
                    ret, cv_img = cap.read()
                    if ret:
                        # 이미지 처리 로직
                        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                        results = hands.process(cv_img)
                        results_pose = pose.process(cv_img)

                        if results.multi_hand_landmarks:
                            for hand_landmarks in results.multi_hand_landmarks:
                                xyz_list = []
                                for i, landmark in enumerate(hand_landmarks.landmark):
                                    row = [landmark.x - hand_landmarks.landmark[0].x,
                                           landmark.y - hand_landmarks.landmark[0].y,
                                           landmark.z - hand_landmarks.landmark[0].z]
                                    xyz_list.append(row)

                                arr = np.array(xyz_list).reshape(1, 21, 3)
                                yhat = model.predict(arr, verbose=0)[0]
                                result = np.argmax(yhat)
                                detected_word = data_dict[result]  # 검출된 단어
                                self.update_word_signal.emit(detected_word)

                        # QImage로 변환
                        qt_img = self.main_app.convert_cv_qt(cv_img)  # MyApp 클래스의 메서드 호출
                        self.change_pixmap_signal.emit(qt_img)

        cap.release()

class MyApp(QDialog):
    def __init__(self):
        super().__init__()
        # Qt Designer에서 만든 UI 파일 로드
        uic.loadUi('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/result/drl_demo.ui', self)  # .ui 파일 경로를 여기에 적어주세요

        # 카메라 스레드 설정
        self.cam_thread = CameraThread(self)
        self.cam_thread.change_pixmap_signal.connect(self.update_image)
        self.cam_thread.update_word_signal.connect(self.receive_word)
        self.cam_thread.start()


        #Qt Merge
        self.autoword_1.setVisible(False)
        self.autoword_2.setVisible(False)
        self.autoword_3.setVisible(False)
        self.autoword_4.setVisible(False)
        self.autoword_5.setVisible(False)
        self.text = ""
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
        
        # QTimer 객체 생성
        self.timer = QTimer(self)
        # QTimer 이벤트와 연결할 함수 설정
        self.timer.timeout.connect(self.update_word)
        # 0.5초마다 타이머를 시작
        self.timer.start(300)  # 500ms = 0.5초
        
        self.autoword_1.clicked.connect(self.changeText_1)
        self.autoword_2.clicked.connect(self.changeText_2)
        self.autoword_3.clicked.connect(self.changeText_3)
        self.autoword_4.clicked.connect(self.changeText_4)
        self.autoword_5.clicked.connect(self.changeText_5)
        self.btn_reset.clicked.connect(self.reset_line)
        self.word_list = []
        self.last_word_time = time.time()  # 초기화 시간 설정

    def receive_word(self, word):
        # 이미 값을 읽었다면 더 이상 처리하지 않습니다.

        # 카메라 스레드에서 단어를 전달받는 함수
        self.word = word
        # 이미 값을 읽었음을 플래그로 표시합니다.
        
    def update_image(self, qt_img):
        # QLabel에 이미지 표시
        self.camera_screen.setPixmap(QPixmap.fromImage(qt_img))  # 'camera_screen'은 QLabel의 objectName
    
    
    def update_word(self):
        if hasattr(self, 'word') and self.word:  # 단어가 존재하고 값이 비어있지 않은 경우에만 실행
            self.word_list.append(self.word)
            self.word = ""
            print(self.word_list)

            # 입력 리스트에 다섯 개의 값이 쌓였을 경우
            if len(self.word_list) >= 5:
                output = max(set(self.word_list), key=self.word_list.count)

                self.word_list = []
            
                if output == 'space':
                    self.text += " "
                elif output == 'backspace':
                    # 마지막 문자를 제거합니다.
                    self.text = self.text[:-1]
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
        
            self.last_word_time = time.time()

        else:
            self.word_list = []
            
        # def Merge
    def reset_line(self):
        self.input.clear()  # Line edit의 문자열을 삭제합니다.

    def speech_word(self, word_to_speech) :
        tts_ko = gTTS(text=word_to_speech, lang='ko')
        tts_ko.save(self.file_name)
        playsound(self.file_name)

    def add_word(self, input_word):
        if input_word.strip():  # 입력된 단어가 공백이 아닌지 확인
            word_df = pd.read_csv('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/result/autocorrect.csv')  # 여기서 CSV 파일 경로 수정
            if input_word in word_df['word'].values:
                index = word_df.index[word_df['word'] == input_word].tolist()
                word_df['frequency'][index] += 1
                print("fre")
            else:
                word_df.loc[len(word_df)] = [input_word, 1]
                print("word")

            word_df.to_csv('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/result/autocorrect.csv', index=False)

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
    #img update
    def convert_cv_qt(cv_img):
        cv_img_flipped = cv2.flip(cv_img, 1)
        
        rgb_image = cv2.cvtColor(cv_img_flipped, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        return p
            
    def on_text_changed(self):
        self.word_df=pd.read_csv('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/result/autocorrect.csv')
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
                print("Space 입력이 감지되었습니다.")
                self.prefix = self.text.split(" ")[-2]
                print(self.prefix)
                self.speech_word(self.prefix)
                self.add_word(self.prefix)
            else:
                
                self.prefix = self.text.split(" ")[-1]
                #print(self.prefix)
                
                 
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyApp()
    widget.show()
    sys.exit(app.exec())