# mediapipe_thread.py

# from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import time
import mediapipe as mp
from tensorflow.keras.models import load_model
import numpy as np
from camera_thread import *
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import cv2
import time
from queue import Queue

camera_image_queue = Queue(maxsize=1)  # 이미지를 저장하는 이미지 큐

class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    time.sleep(0.2)

    def __init__(self, camera_sender):
        super().__init__()
        self.camera_sender = camera_sender
        
    def run(self):
        time.sleep(0.5)
        last_image_time = time.time()

        while True:
            cv_img = self.camera_sender._get_frame()
            if cv_img is None:
                continue

            current_time = time.time()
            if not camera_image_queue.empty():
                camera_image_queue.get()
            if current_time - last_image_time >= 0.05:
                camera_image_queue.put(cv_img)
                last_image_time = current_time

            cv_img = cv2.flip(cv_img, 1)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            qt_img = QImage(cv_img.data, cv_img.shape[1], cv_img.shape[0],QImage.Format.Format_RGB888)
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
        mp_hands = mp.solutions.hands
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles

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

        # start_time = time.time()
        yhat = self.model.predict(arr, verbose=0)[0]
        # end_time = time.time()
        # print("오른손 작업에 소요된 시간:", end_time - start_time, "초")

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
        left_hand_data_dict = {31 : "backspace", 32 : "1", 33 : "2", 34 : "3", 35 : "4",
                               36 : "5", 37 : "question", 38 : "shift", 39 : "space"}
        xyz_list = []
        for landmark in landmarks.landmark:
            row = [landmark.x - landmarks.landmark[0].x, landmark.y - landmarks.landmark[0].y, landmark.z - landmarks.landmark[0].z]
            xyz_list.append(row)
        
        arr = np.array(xyz_list)
        arr = arr.reshape(1, 21, 3)
        # start_time = time.time()
        
        yhat = self.model.predict(arr, verbose=0)[0]
        # end_time = time.time()
        # print("왼손 작업에 소요된 시간:", end_time - start_time, "초")

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
    def run(self):
        self._is_running = True  # 스레드가 시작될 때 실행 여부 변수를 True로 설정
        command1 = None
        command2 = None
        mp_hands = mp.solutions.hands
        mp_pose = mp.solutions.pose
        with mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7) as hands, \
            mp_pose.Pose(
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
                
                if results.multi_hand_landmarks and right_hand_num != None:
                    command1 = self.right_hand_command(results.multi_hand_landmarks[right_hand_num])
                    self.update_word_signal.emit(command1)
                elif results.multi_hand_landmarks and left_hand_num != None:
                    command2 = self.left_hand_command(results.multi_hand_landmarks[left_hand_num])
                    self.update_word_signal.emit(command2)
                # end_time = time.time()
        

    def stop(self):
        self._is_running = False 