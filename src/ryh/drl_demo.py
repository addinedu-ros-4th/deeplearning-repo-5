from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QLineEdit,QDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage
import sys
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import mediapipe as mp
from PyQt6 import uic

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
        model = load_model('/home/ryu/amr_ws/ml_drl/deeplearning-repo-5/src/ryh/handModel.h5')  # 모델 경로 설정

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
                        qt_img = self.convert_cv_qt(cv_img)
                        self.change_pixmap_signal.emit(qt_img)

        cap.release()

    @staticmethod
    def convert_cv_qt(cv_img):
        """ OpenCV 이미지를 QPixmap으로 변환합니다. """
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        return p

class MyApp(QDialog):
    def __init__(self):
        super().__init__()
        # Qt Designer에서 만든 UI 파일 로드
        uic.loadUi('/home/ryu/amr_ws/ml_drl/deeplearning-repo-5/src/ryh/drl_demo.ui', self)  # .ui 파일 경로를 여기에 적어주세요

        # 카메라 스레드 설정
        self.cam_thread = CameraThread()
        self.cam_thread.change_pixmap_signal.connect(self.update_image)
        self.cam_thread.update_word_signal.connect(self.update_word)
        self.cam_thread.start()

    def update_image(self, qt_img):
        # QLabel에 이미지 표시
        self.camera_screen.setPixmap(QPixmap.fromImage(qt_img))  # 'camera_screen'은 QLabel의 objectName

    def update_word(self, word):
        # QLineEdit에 텍스트 업데이트
        self.word.setText(word)  # 'word'는 QLineEdit의 objectName

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyApp()
    widget.show()
    sys.exit(app.exec())