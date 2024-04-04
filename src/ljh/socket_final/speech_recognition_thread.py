from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class SpeechRecognitionThread(QThread):
    recognition_result = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.r = sr.Recognizer()
        self.audio_source = sr.Microphone()
        self.is_running = False

    def run(self):
        self.is_running = True
        while self.is_running:
            with self.audio_source as source:
                print("듣고있어요")
                audio = self.r.listen(source, phrase_time_limit=3)

            try:
                text = self.r.recognize_google(audio, language='ko')
                print(text)
                if text != "":
                    self.recognition_result.emit(text)

            except sr.UnknownValueError:
                print("인식 실패")
            except sr.RequestError as e:
                print('요청 실패 : {0}'.format(e))    #api, network error
    
    def stop(self):
        self.is_running = False