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

#'0', '1', '10', '11', '12', '13', '14', '15', '16', '17', 
#'18', '19', '2', '20', '21', '22', '23', '24', '25', '26', 
#'27', '28', '29', '3', '30', '4', '5', '6', '7', '8',
# '9', 'backspace', 'question', 'shift', 'space'
#ㄱ ㄴ ㅋ ㅌ ㅍ ㅎ ㅏ ㅑ ㅓ ㅕ
#ㅗ ㅛ ㄷ ㅜ ㅠ ㅡ ㅣ ㅐ ㅔ ㅚ
#ㅟ ㅒ ㅖ ㄹ ㅢ ㅁ ㅂ ㅅ ㅇ ㅈ
#ㅊ 

cap = cv2.VideoCapture(0)
count = 0
old_key = 0
font = cv2.FONT_HERSHEY_PLAIN
font_scale = 1
color = (255, 255, 0)



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


def get_body_points(results_pose) :# pose에서 손목 좌표 반환
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


def right_hand_command(landmarks): #오른손 인식
    result = None
    right_hand_data_dict = {0 : "ㄱ", 1 : "ㄴ", 2 : "ㅋ", 3 : "ㅌ", 4 : "ㅍ", 
             5 : "ㅎ", 6 : "ㅏ", 7 : "ㅑ", 8 : "ㅓ", 9 : "ㅕ",
             10 : "ㅗ", 11 : "ㅛ", 12 : "ㄷ", 13 : "ㅜ", 14 : "ㅠ",
             15 : "ㅡ", 16 : "ㅣ", 17 : "ㅐ", 18 : "ㅔ", 19 : "ㅚ",
             20 : "ㅟ", 21 : "ㅒ", 22 : "ㅖ", 23 : "ㄹ", 24 : "ㅢ",
             25 : "ㅁ", 26 : "ㅂ", 27 : "ㅅ", 28 : "ㅇ", 29 : "ㅈ",
             30 : "ㅊ"}
    xyz_list = []
    for i, landmark in enumerate(landmarks.landmark):
        row = [landmark.x - landmarks.landmark[0].x, landmark.y - landmarks.landmark[0].y, landmark.z - landmarks.landmark[0].z]
        xyz_list.append(row)
    
    arr = np.array(xyz_list)
    arr = arr.reshape(1, 21, 3)
    yhat = model.predict(arr, verbose=0)[0]
    if np.max(yhat) > 0.8 : # 출력 문턱값
        try :
            result = right_hand_data_dict[np.argmax(yhat)]
        except : 
            pass
    return result
    

def left_hand_command(landmarks):
    result = None
    left_hand_data_dict = {31 : "backspace", 32 : "question", 33 : "shift", 34 : "space"}
    xyz_list = []
    for i, landmark in enumerate(landmarks.landmark):
        row = [landmark.x - landmarks.landmark[0].x, landmark.y - landmarks.landmark[0].y, landmark.z - landmarks.landmark[0].z]
        xyz_list.append(row)
    
    arr = np.array(xyz_list)
    arr = arr.reshape(1, 21, 3)
    yhat = model.predict(arr, verbose=0)[0]
    if np.max(yhat) > 0.9 : # 출력 문턱값
        try :
            result = left_hand_data_dict[np.argmax(yhat)]
        except :
            pass
    return result

    

def hand_direction_detection(results_pose, results) : #손 방향 인식하고 각 손의 랜드마크 인덱스 반환
    right_hand_num = None
    left_hand_num = None
    if results.multi_hand_landmarks :
        left_hand, right_hand = get_body_points(results_pose)


        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand = [hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y, hand_landmarks.landmark[0].z]

            lenth_L = (abs(hand[0] - left_hand[0]) ** 2 + abs(hand[1] - left_hand[1]) ** 2) ** 0.5
            lenth_R = (abs(hand[0] - right_hand[0]) ** 2 + abs(hand[1] - right_hand[1]) ** 2) ** 0.5
            
            if lenth_L < lenth_R :
                left_hand_num = idx
            else : 
                right_hand_num = idx

            
    return left_hand_num, right_hand_num
    
    



    
    
def main():
    try :
        with mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4) as hands:

            with mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.4,
                min_tracking_confidence=0.4) as pose:

                while cap.isOpened():
                    command1 = None
                    command2 = None
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
                    

                    # image = draw_landmarks(results_pose, results, image)# 랜드마크 그리기
                    left_hand_num, right_hand_num = hand_direction_detection(results_pose, results)
                    
                    if results.multi_hand_landmarks:
                        if right_hand_num != None:
                            command1 = right_hand_command(results.multi_hand_landmarks[right_hand_num])
                        
                        if left_hand_num != None:
                            command2 = left_hand_command(results.multi_hand_landmarks[left_hand_num])
                        
                        print(command2, command1)
                        
                        
                    
                            
                    #보기 편하게 이미지를 좌우 반전합니다.
                    cv2.imshow('Demo', cv2.flip(image, 1))
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
    except Exception as e:
        print(e)
    cap.release()

if __name__ == "__main__" :
    main()
