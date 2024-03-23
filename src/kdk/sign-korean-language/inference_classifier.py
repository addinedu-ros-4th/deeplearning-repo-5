import pickle
import cv2
import mediapipe as mp
import numpy as np
from PIL import ImageFont, ImageDraw, Image

# Load the model
model_dict = pickle.load(open('/home/kkyu/amr_ws/DL/project_deep/sign-korean-language/model.p', 'rb'))
model = model_dict['model']

# Video capture without flipping
cap = cv2.VideoCapture('/dev/video0')
# cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

# Mediapipe hands initialization
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

labels_dict = {
    0: 'ㄱ',
    1: 'ㄴ',
    2: 'ㄷ',
}

# Font settings
font_path = "/usr/share/fonts/truetype/nanum/NanumSquare_acR.ttf"
font_size = 40
font = ImageFont.truetype(font_path, font_size)

# Previous hand landmarks coordinates
prev_hand_landmarks = None

while True:
    data_aux = []

    ret, frame = cap.read()

    H, W, _ = frame.shape

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(frame_rgb)
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]  # Accessing the first detected hand

        # Concatenate current hand landmarks with previous ones if available
        if prev_hand_landmarks:
            combined_landmarks = np.concatenate((prev_hand_landmarks, hand_landmarks), axis=0)
        else:
            combined_landmarks = hand_landmarks

        # Store the current hand landmarks for future use
        prev_hand_landmarks = None

        # Extract x and y coordinates of combined hand landmarks
        for landmark in combined_landmarks.landmark:
            data_aux.extend([landmark.x, landmark.y])

        # Perform prediction using the model
        data_aux = np.array(data_aux).reshape(1, -1)
        prediction = model.predict(data_aux)
        predicted_character = labels_dict[int(prediction[0])]

        # Create a PIL image from the OpenCV frame
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_frame)

        # Adjust the y-coordinate for text position to avoid overlap with the rectangle
        x_ = [landmark.x for landmark in hand_landmarks.landmark]
        y_ = [landmark.y for landmark in hand_landmarks.landmark]
        x1 = int(min(x_) * W) - 10
        y1 = int(min(y_) * H) - 10
        x2 = int(max(x_) * W) - 10
        y2 = int(max(y_) * H) - 10
        text_position_y = y1 - 10 if y1 - 10 >= 0 else y2 + 10

        # Draw the rectangle and text with blue font color
        draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 0, 0), width=4)
        draw.text((x1, text_position_y), predicted_character, font=font, fill=(0, 0, 255))  # Blue color

        # Convert the PIL image back to OpenCV format
        frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
