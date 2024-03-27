import cv2
import numpy as np
import time
import tensorflow as tf
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image


from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# 웹캠을 켭니다.
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()  # 웹캠에서 프레임을 읽습니다.

    # 프레임을 모델이 요구하는 입력 크기로 변경합니다.
    img = cv2.resize(frame, (224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    # 예측을 수행합니다.
    start_time = time.time()
    with tf.device('/GPU:0'):
        preds = model.predict(img)
    end_time = time.time()
    print("작업에 소요된 시간:", end_time - start_time, "초")
    # 상위 3개의 예측 결과를 가져옵니다.
    top_preds = decode_predictions(preds, top=3)[0]

    # 결과를 화면에 출력합니다.
    for i, (imagenet_id, label, score) in enumerate(top_preds):
        text = '{}: {:.2f}%'.format(label, score * 100)
        cv2.putText(frame, text, (10, (i + 1) * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # 화면에 프레임을 표시합니다.
    cv2.imshow('Webcam - VGG Prediction', frame)

    # 'q' 키를 누르면 종료합니다.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 작업을 정리하고 웹캠을 닫습니다.
cap.release()
cv2.destroyAllWindows()
