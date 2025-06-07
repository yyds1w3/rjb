import cv2
import dlib
import numpy as np
import time
import mediapipe as mp
from tensorflow.keras.models import load_model

# ----------------------
# 模型初始化
# ----------------------
# 人脸检测与关键点
face_detector = dlib.get_frontal_face_detector()
landmark_predictor = dlib.shape_predictor(r"E:\model\dlib\shape_predictor_68_face_landmarks (1).dat")

# 情绪识别模型
emotion_model = load_model(r"E:\model\dlib\emotion_detection_model.h5")
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

# 肢体语言识别（MediaPipe BlazePose）
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 肢体语言分类器
def classify_gesture(landmarks):
    # 从 numpy 数组中提取关键点坐标 (x, y)
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
    right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]

    # 使用索引访问 x 和 y 坐标
    if right_elbow[1] < right_shoulder[1] and abs(right_wrist[0] - right_shoulder[0]) > 0.2 * landmarks.shape[1]:
        return "Waving"
    else:
        return "Neutral"

# ----------------------
# 图像处理函数
# ----------------------
def preprocess_face(face_img):
    # 情绪识别预处理
    face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    face_img = cv2.resize(face_img, (48, 48))
    face_img = np.expand_dims(face_img, axis=(0, -1)) / 255.0
    return face_img

# 修正后的姿态检测函数
def detect_pose(frame):
    results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return results.pose_landmarks  # 直接返回 pose_landmarks 对象

# ----------------------
# 主程序流程
# ----------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
prev_time = 0

# 初始化情绪计数器
emotion_counts = {label: 0 for label in emotion_labels}
total_frames = 0

# 显示启动提示
print("The multimodal human analysis system has been launched")
print("--------------------------------")
print("Real - time emotion and gesture analysis is in progress...")
print("Press the Enter key to terminate the analysis and view the emotion statistics results.")
print("--------------------------------")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 基础处理
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ----------------------
    # 人脸与情绪识别
    # ----------------------
    faces = face_detector(gray)
    current_emotion = "None"

    for face in faces:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # 情绪识别
        face_roi = frame[y:y + h, x:x + w]
        processed_face = preprocess_face(face_roi)
        emotion_pred = emotion_model.predict(processed_face)
        emotion_idx = np.argmax(emotion_pred)
        current_emotion = emotion_labels[emotion_idx]

        cv2.putText(frame, f"Emotion: {current_emotion}",
                    (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # 绘制人脸关键点
        landmarks = landmark_predictor(gray, face)
        for n in range(68):
            cv2.circle(frame, (landmarks.part(n).x, landmarks.part(n).y),
                       2, (0, 0, 255), -1)

    # 更新情绪计数
    if current_emotion != "None":
        emotion_counts[current_emotion] += 1
        total_frames += 1

    # ----------------------
    # 肢体语言识别
    # ----------------------
    pose_landmarks = detect_pose(frame_rgb)
    if pose_landmarks:
        # 修正：从 pose_landmarks.landmark 中提取坐标
        h, w, _ = frame.shape
        landmarks = np.array([[lm.x * w, lm.y * h] for lm in pose_landmarks.landmark])

        # 分类肢体语言
        gesture = classify_gesture(landmarks)
        cv2.putText(frame, f"Gesture: {gesture}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        # 绘制姿态骨架
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(
            frame, pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
        )

    # 绘制FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 显示提示信息
    cv2.putText(frame, "Press Enter to exit and show emotion statistics", (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Multi-Modal Human Analysis", frame)

    # 检测按键事件（回车）
    key = cv2.waitKey(1)
    if key == 13:  # 回车键的 ASCII 码是 13
        break
    elif key & 0xFF == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        exit()

cap.release()
cv2.destroyAllWindows()

# 显示情绪统计结果
print("\nStatistical results of sentiment analysis")
print("--------------------------------")
if total_frames > 0:
    for emotion, count in emotion_counts.items():
        percentage = (count / total_frames) * 100
        print(f"{emotion}: {count} 帧 ({percentage:.2f}%)")
else:
    print("No face detected")
print("--------------------------------")
