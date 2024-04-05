from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import uic
import sys
from mediapipe_thread import *
from speech_recognition_thread import *
import pandas as pd
import time
import asyncio
import qasync
from trie import Trie
from jamo import j2hcj, h2j
from gtts import gTTS
from playsound import playsound
from jamos import cons, vowels, cons_double, double_cons, gesture2text



class MyApp(QDialog):
    def __init__(self):
        super().__init__()
        self.csv_path = "/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/total/autocorrect.csv"
        uic.loadUi('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/total/drl_demo.ui', self)  # .ui 파일 경로를 여기에 적어주세요
        self.speech_recognition_thread = SpeechRecognitionThread()
        self.speech_recognition_thread.recognition_result.connect(self.on_recognition_result)
        self.mediapipe_thread = MediapipeThread('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/total/handModel.h5')
        self.mediapipe_thread.update_word_signal.connect(self.update_word_label)

        self.camera_thread = CameraThread(self.HTT)      
        self.camera_thread.change_pixmap_signal.connect(self.update_camera_screen)
        self.camera_thread.start()
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

        self.show()

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
                    self.speech_word(self.text)
                    for word in self.text.split(" "):
                        self.add_word(word)
                    self.text = ""
                    self.input.setText(self.text)
                else:
                    print("Space 입력이 감지되었습니다.")
                    self.prefix = self.text.split(" ")[-2]
                    print(self.prefix)
                    self.speech_word(self.prefix)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyApp()
    widget.show()

    loop = qasync.QEventLoop(app)           #종료 권한 관리
    asyncio.set_event_loop(loop)

    # sys.exit(app.exec())
    loop.run_forever() 