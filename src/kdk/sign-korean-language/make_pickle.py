# import cv2
# import mediapipe as mp

# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose()
# mp_drawing = mp.solutions.drawing_utils




# cap = cv2.VideoCapture(0)

# while cap.isOpened():
#     ret, frame = cap.read()
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     result = pose.process(rgb_frame)

#     annotated_frame = frame.copy()
#     mp_drawing.draw_landmarks(annotated_frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
#     cv2.imshow('Pose Estimation', annotated_frame)

#     if cv2.waitKey(5) & 0xFF == 27:
#         break



# cap.release()
# cv2.destroyAllWindows()
















import cv2
import os
import numpy as np
import pandas as pd
import mediapipe as mp
import time
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# 이미지 파일의 경우을 사용하세요.:
# path = '/home/rds/Desktop/git_ws/sign-korean-language/data'
# for file_name in os.listdir(path):
#     file_name = file_name +"/"
#     IMAGE_FILES = os.listdir(path + file_name)

#     with mp_hands.Hands(
#         static_image_mode=True,
#         max_num_hands=2,
#         min_detection_confidence=0.5) as hands:
#         for idx, file in enumerate(IMAGE_FILES):
#             # 이미지를 읽어 들이고, 보기 편하게 이미지를 좌우 반전합니다.
#             image = cv2.flip(cv2.imread(path + file_name + file), 1)
#             Null_image = np.zeros_like(image)
#             # 작업 전에 BGR 이미지를 RGB로 변환합니다.
#             results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
#             # 손으로 프린트하고 이미지에 손 랜드마크를 그립니다.
#             print('Handedness:', results.multi_handedness)
#             if not results.multi_hand_landmarks:
#                 continue
#             image_height, image_width, _ = image.shape
#             annotated_image = image.copy()
#             for hand_landmarks in results.multi_hand_landmarks:
#                 print('hand_landmarks:', hand_landmarks)
#                 print(
#                     f'Index finger tip coordinates: (',
#                     f'{hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * image_width}, '
#                     f'{hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * image_height})'
#                 )
#                 mp_drawing.draw_landmarks(
#                     Null_image,
#                     hand_landmarks,
#                     mp_hands.HAND_CONNECTIONS,
#                     mp_drawing_styles.get_default_hand_landmarks_style(),
#                     mp_drawing_styles.get_default_hand_connections_style())
#             cv2.imwrite(path +
#                 '/tmp_' + file_name + str(idx) + '.png', cv2.flip(Null_image, 1))

# 웹캠, 영상 파일의 경우 이것을 사용하세요.:

xy_df = pd.DataFrame(columns=["x", "y", "z"])
cap = cv2.VideoCapture('/dev/video0')
count = 0
old_key = 0
DATA_DIR = '/home/kkyu/amr_ws/DL/project_deep/sign-korean-language/data/ㅕ/'
with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("카메라를 찾을 수 없습니다.")# 동영상을 불러올 경우는 'continue' 대신 'break'를 사용합니다.
            break

        # 필요에 따라 성능 향상을 위해 이미지 작성을 불가능함으로 기본 설정합니다.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        Null_image = np.zeros_like(image)
        # 이미지에 손 주석을 그립니다.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        new_image = np.copy(image)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

            if cv2.waitKey(5) & 0xFF == 97 :
                for i, landmark in enumerate(hand_landmarks.landmark):
                    row = [landmark.x - hand_landmarks.landmark[0].x, landmark.y - hand_landmarks.landmark[0].y, landmark.z - hand_landmarks.landmark[0].z]
                    xy_df.loc[len(xy_df)] = row
                
                xy_df.tail(21).to_pickle(os.path.join(DATA_DIR + f'{count}.pickle'))
                count += 1
                print(count)
                time.sleep(0.5)

            if cv2.waitKey(5) & 0xFF == 113:
                pass

                
        #보기 편하게 이미지를 좌우 반전합니다.
        cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()


#ㄴ, ㄷ, ㄹ, ㅈ, ㅊ, ㅏ, ㅑ, ㅓ, ㅕ










































