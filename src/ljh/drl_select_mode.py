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
from queue import Queue

camera_image_queue = Queue()  # 이미지를 저장하는 이미지 큐

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

    def __init__(self):
        super().__init__()

    def run(self):
        cap = cv2.VideoCapture(0)
        last_image_time = time.time()

        while True:
            ret, cv_img = cap.read()
            if ret:
                current_time = time.time()
                
                if current_time - last_image_time >= 0.05:
                    camera_image_queue.put(cv_img)
                    last_image_time = current_time
                    
                cv_img = cv2.flip(cv_img, 1)      
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                height, width, channel = cv_img.shape
                qt_img = QImage(cv_img.data, width, height, QImage.Format.Format_RGB888)
                self.change_pixmap_signal.emit(qt_img)
                
    def stop(self):
        self._is_running = False

class MediapipeThread(QThread):
    update_word_signal = pyqtSignal(str)

    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path
        self._is_running = False  # 스레드 실행 여부를 나타내는 변수
        self.model = load_model(self.model_path)

    def draw_landmarks(self, results_pose, results, image):
        self.mp_drawing.draw_landmarks(
                    image,
                    results_pose.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style())

        return image


    def get_body_points(self, results_pose) :# pose에서 손목 좌표 반환
        noen_num = 999
        if results_pose.pose_landmarks :
            try :
                left_hand = [results_pose.pose_landmarks.landmark[15].x,
                            results_pose.pose_landmarks.landmark[15].y,
                                results_pose.pose_landmarks.landmark[15].z]
            except :
                left_hand = [noen_num,noen_num,noen_num]
            try :
                right_hand = [results_pose.pose_landmarks.landmark[16].x,
                            results_pose.pose_landmarks.landmark[16].y,
                                results_pose.pose_landmarks.landmark[16].z]
            except :
                right_hand = [noen_num,noen_num,noen_num]
        else :
            left_hand = [noen_num,noen_num,noen_num]
            right_hand = [noen_num,noen_num,noen_num]
        
        return left_hand, right_hand


    def right_hand_command(self, landmarks): #오른손 인식

        right_hand_data_dict = {
            0 : "ㄱ", 1 : "ㄴ", 2 : "ㅋ", 3 : "ㅌ", 4 : "ㅍ", 
            5 : "ㅎ", 6 : "ㅏ", 7 : "ㅑ", 8 : "ㅓ", 9 : "ㅕ",
            10 : "ㅗ", 11 : "ㅛ", 12 : "ㄷ", 13 : "ㅜ", 14 : "ㅠ",
            15 : "ㅡ", 16 : "ㅣ", 17 : "ㅐ", 18 : "ㅔ", 19 : "ㅚ",
            20 : "ㅟ", 21 : "ㅒ", 22 : "ㅖ", 23 : "ㄹ", 24 : "ㅢ",
            25 : "ㅁ", 26 : "ㅂ", 27 : "ㅅ", 28 : "ㅇ", 29 : "ㅈ",
            30 : "ㅊ"}
        xyz_list = []
        for landmark in landmarks.landmark :
            row = [landmark.x - landmarks.landmark[0].x, landmark.y - landmarks.landmark[0].y, landmark.z - landmarks.landmark[0].z]
            xyz_list.append(row)
        
        arr = np.array(xyz_list)
        arr = arr.reshape(1, 21, 3)

        start_time = time.time()
        yhat = self.model.predict(arr, verbose=0)[0]
        end_time = time.time()
        print("오른손 작업에 소요된 시간:", end_time - start_time, "초")

        if np.max(yhat) > 0.7 : # 출력 문턱값
            try :
                result = right_hand_data_dict[np.argmax(yhat)]
            except : 
                result = None
        else :
            result = None
        
        return result
        

    def left_hand_command(self, landmarks):
        result = None
        left_hand_data_dict = {31 : "backspace", 32 : "question", 33 : "shift", 34 : "space"}
        xyz_list = []
        for landmark in landmarks.landmark:
            row = [landmark.x - landmarks.landmark[0].x, landmark.y - landmarks.landmark[0].y, landmark.z - landmarks.landmark[0].z]
            xyz_list.append(row)
        
        arr = np.array(xyz_list)
        arr = arr.reshape(1, 21, 3)
        start_time = time.time()
        
        yhat = self.model.predict(arr, verbose=0)[0]
        end_time = time.time()
        print("왼손 작업에 소요된 시간:", end_time - start_time, "초")

        if np.max(yhat) > 0.9 : # 출력 문턱값
            try :
                result = left_hand_data_dict[np.argmax(yhat)]
            except :
                result = None
        return result

        

    def hand_direction_detection(self, results_pose, results) : #손 방향 인식하고 각 손의 랜드마크 인덱스 반환
        right_hand_num = None
        left_hand_num = None
        if results.multi_hand_landmarks :
            left_hand, right_hand = self.get_body_points(results_pose)


            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand = [hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y, hand_landmarks.landmark[0].z]
                # print(hand)
                lenth_L = (abs(hand[0] - left_hand[0]) ** 2 + abs(hand[1] - left_hand[1]) ** 2) ** 0.5
                lenth_R = (abs(hand[0] - right_hand[0]) ** 2 + abs(hand[1] - right_hand[1]) ** 2) ** 0.5
                
                if lenth_L < lenth_R :
                    left_hand_num = idx
                else : 
                    right_hand_num = idx

                
        return left_hand_num, right_hand_num
    def run(self):####################################### 스레드 에러
        self._is_running = True  # 스레드가 시작될 때 실행 여부 변수를 True로 설정
        command1 = None
        command2 = None
        with mp.solutions.hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7) as hands, \
            mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5) as pose:
            while self._is_running:
                cv_img = camera_image_queue.get()
                # 이미지 처리 로직
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                results = hands.process(cv_img)
                results_pose = pose.process(cv_img)
                left_hand_num, right_hand_num = self.hand_direction_detection(results_pose, results)
                if results.multi_hand_landmarks:
                    if right_hand_num != None:
                        command1 = self.right_hand_command(results.multi_hand_landmarks[right_hand_num])
                        self.update_word_signal.emit(command1)
                        
                    if left_hand_num != None:
                        command2 = self.left_hand_command(results.multi_hand_landmarks[left_hand_num])
                        self.update_word_signal.emit(command2)
        
        

    def stop(self):
        self._is_running = False



class MyApp(QDialog):
    def __init__(self):
        super().__init__()
        # Qt Designer에서 만든 UI 파일 로드
        uic.loadUi('/home/hj/amr_ws/ML_DL/src/project/yhj/result/drl_demo.ui', self)  # .ui 파일 경로를 여기에 적어주세요

        # CameraThread 및 MediapipeThread 초기화
        self.camera_thread = CameraThread()
        self.mediapipe_thread = MediapipeThread('/home/rds/Desktop/git_ws/deeplearning-repo-5/src/ljh/handModel.h5')
        # 카메라 이미지 업데이트 신호를 받으면 화면에 표시
        self.camera_thread.change_pixmap_signal.connect(self.update_camera_screen)
        # Mediapipe에서 업데이트된 단어를 받으면 해당 레이블에 표시
        self.mediapipe_thread.update_word_signal.connect(self.update_word_label)
        
        # 카메라 및 Mediapipe 스레드 시작
        self.camera_thread.start()
    
        self.autoword_1.setVisible(False)
        self.autoword_2.setVisible(False)
        self.autoword_3.setVisible(False)
        self.autoword_4.setVisible(False)
        self.autoword_5.setVisible(False)
        self.text = ""
        self.prefix = ""
        self.csv_name = "/home/hj/amr_ws/ML_DL/src/project/yhj/result/autocorrect.csv"
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
        self.timer.start(1)  # 500ms = 0.5초
        
        self.autoword_1.clicked.connect(self.changeText_1)
        self.autoword_2.clicked.connect(self.changeText_2)
        self.autoword_3.clicked.connect(self.changeText_3)
        self.autoword_4.clicked.connect(self.changeText_4)
        self.autoword_5.clicked.connect(self.changeText_5)
        self.btn_reset.clicked.connect(self.reset_line)
        self.word_list = []
        self.last_word_time = time.time()  # 초기화 시간 설정
        
        self.HTT.toggled.connect(self.on_radio_toggled)
        self.STT.toggled.connect(self.on_radio_toggled)

    def speech_to_text(self):
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print("듣고있어요")
                audio = r.listen(source)
                
            try :
                #text = r.recognize_google(audio, language='en-US')
                text = r.recognize_google(audio, language='ko')
                print(text)
                self.input.setText(self.text)  # 'word'는 QLineEdit의 objectName
                
            except sr.UnknownValueError:
                print("인식 실패")
            except sr.RequestError as e:
                print('요청 실패 : {0}'.format(e))

    def on_radio_toggled(self):
        sender = self.sender()
        if sender.isChecked():
            if sender == self.HTT:
                self.STT.setChecked(False)
                if not self.mediapipe_thread.isRunning():  # 스레드가 실행 중이 아닌 경우에만 시작
                    self.mediapipe_thread.start()
            elif sender == self.STT:
                self.HTT.setChecked(False)
                self.mediapipe_thread.stop() 
                self.speech_to_text()
        
    def on_key_press_event(self, event):
        if event.key() == Qt.Key.Key_Escape:
            # MediapipeThread 스레드 종료
            self.camera_thread.stop()
            self.mediapipe_thread.stop()
            # PyQt6 애플리케이션 종료
            self.close()
        else:
            # 다른 키가 눌렸을 때의 동작
            pass
    def update_word(self):
        if hasattr(self, 'word') and self.word:  # 단어가 존재하고 값이 비어있지 않은 경우에만 실행
            self.word_list.append(self.word)
            self.word = ""
            print(self.word_list)

            # 입력 리스트에 다섯 개의 값이 쌓였을 경우
            if len(self.word_list) >= 15:
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
        
        elif time.time() - self.last_word_time >= 0.3:  # self.word가 0.3초 동안 존재하지 않으면
            self.word_list = []  
    
    def reset_line(self):
        self.input.clear()  # Line edit의 문자열을 삭제합니다.

    def speech_word(self, word_to_speech) :
        tts_ko = gTTS(text=word_to_speech, lang='ko')
        tts_ko.save(self.file_name)
        playsound(self.file_name)

    def add_word(self, input_word):
        if input_word.strip():  # 입력된 단어가 공백이 아닌지 확인
            word_df = pd.read_csv(self.csv_name)  # 여기서 CSV 파일 경로 수정
            if input_word in word_df['word'].values:
                index = word_df.index[word_df['word'] == input_word].tolist()
                word_df['frequency'][index] += 1
                print("fre")
            else:
                word_df.loc[len(word_df)] = [input_word, 1]
                print("word")

            word_df.to_csv(self.csv_name, index=False)
    
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
        self.word_df=pd.read_csv(self.csv_name)
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