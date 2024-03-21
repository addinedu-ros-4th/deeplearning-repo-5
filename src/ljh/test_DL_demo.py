# import tensorflow as tf
import numpy as np
import pandas as pd
import os
import cv2
import mediapipe as mp
import time

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose


from tensorflow.keras.models import load_model

# 저장된 모델 파일 경로
model_path = "/home/rds/Desktop/git_ws/deeplearning-repo-5/src/ljh/handModel.h5"

# 모델 읽어오기
model = load_model(model_path)

print("test2")

#'0', '1', '10', '11', '12', '13', '14', '15', '16', '17', 
#'18', '19', '2', '20', '21', '22', '23', '24', '25', '26', 
#'27', '28', '29', '3', '30', '4', '5', '6', '7', '8',
# '9', 'backspace', 'question', 'shift', 'space'
#ㄱ ㄴ ㅋ ㅌ ㅍ ㅎ ㅏ ㅑ ㅓ ㅕ
#ㅗ ㅛ ㄷ ㅜ ㅠ ㅡ ㅣ ㅐ ㅔ ㅚ
#ㅟ ㅒ ㅖ ㄹ ㅢ ㅁ ㅂ ㅅ ㅇ ㅈ
#ㅊ 
data_dict = {0 : "ㄱ", 1 : "ㄴ", 2 : "ㅋ", 3 : "ㅌ", 4 : "ㅍ", 
             5 : "ㅎ", 6 : "ㅏ", 7 : "ㅑ", 8 : "ㅓ", 9 : "ㅕ",
             10 : "ㅗ", 11 : "ㅛ", 12 : "ㄷ", 13 : "ㅜ", 14 : "ㅠ",
             15 : "ㅡ", 16 : "ㅣ", 17 : "ㅐ", 18 : "ㅔ", 19 : "ㅚ",
             20 : "ㅟ", 21 : "ㅒ", 22 : "ㅖ", 23 : "ㄹ", 24 : "ㅢ",
             25 : "ㅁ", 26 : "ㅂ", 27 : "ㅅ", 28 : "ㅇ", 29 : "ㅈ",
             30 : "ㅊ", 31 : "backspace", 32 : "question", 33 : "shift", 34 : "space"}
cap = cv2.VideoCapture(0)
count = 0
old_key = 0
font = cv2.FONT_HERSHEY_PLAIN
font_scale = 1
color = (255, 255, 0)
right_hand_num = None
left_hand_num = None


def draw_landmarks(results_pose, results, image):
    mp_drawing.draw_landmarks(
                image,
                results_pose.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
            image,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

    return image


def get_body_points(results_pose):
    left_hand = [results_pose.pose_landmarks[15].x, results_pose.pose_landmarks[15].y, results_pose.pose_landmarks[15].z]
    right_hand = [results_pose.pose_landmarks[16].x, results_pose.pose_landmarks[16].y, results_pose.pose_landmarks[16].z]

    return left_hand, right_hand

def Distinction_hands_direction(results_pose, results):
    left_hand, right_hand = get_body_points(results_pose)

    



    
    
    
with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as hands:
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=True,
        min_detection_confidence=0.5) as pose:
        while cap.isOpened():
            xyz_list = []
            success, image = cap.read()
            if not success:
                print("카메라를 찾을 수 없습니다.")# 동영상을 불러올 경우는 'continue' 대신 'break'를 사용합니다.
                break

            # 필요에 따라 성능 향상을 위해 이미지 작성을 불가능함으로 기본 설정합니다.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            results_pose = pose.process(image)

            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            # new_image = np.copy(image)

            # image = draw_landmarks(results_pose, results, image)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

                
                for i, landmark in enumerate(hand_landmarks.landmark):
                    row = [landmark.x - hand_landmarks.landmark[0].x, landmark.y - hand_landmarks.landmark[0].y, landmark.z - hand_landmarks.landmark[0].z]
                    xyz_list.append(row)
                
                arr = np.array(xyz_list)
                arr = arr.reshape(1, 21, 3)
                yhat = model.predict(arr, verbose=0)[0]
                result = np.argmax(yhat)
                print(data_dict[result])
                # cv2.putText(image, (data_dict[result]), (350, 40), font, font_scale, color, thickness=2)

                
                    
            #보기 편하게 이미지를 좌우 반전합니다.
            cv2.imshow('Demo', cv2.flip(image, 1))
            if cv2.waitKey(1) & 0xFF == 27:
                break
cap.release()