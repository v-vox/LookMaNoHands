import cv2
import mediapipe as mp
import numpy as np
import math

def calculate_ear(eye):
    """
    Calculate the Eye Aspect Ratio (EAR) to detect blinks.
    """
    vertical_1 = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    vertical_2 = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    horizontal = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (vertical_1 + vertical_2) / (2.0 * horizontal)

class FaceDirectionTracker:
    def __init__(self, show_visualization=True):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        
        self.kalman_x = cv2.KalmanFilter(2, 1)
        self.kalman_x.measurementMatrix = np.array([[1, 0]], np.float32)
        self.kalman_x.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self.kalman_x.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.03

        self.kalman_y = cv2.KalmanFilter(2, 1)
        self.kalman_y.measurementMatrix = np.array([[1, 0]], np.float32)
        self.kalman_y.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self.kalman_y.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.03
        
        self.show_visualization = show_visualization
        if show_visualization:
            cv2.namedWindow('Face Direction')
        
        self.cap = None
        self.blink_count = 0
        self.blink_threshold = 0.2  # EAR 
        self.blink_duration = 5  
        self.blink_frame_counter = 0
        
    def start_camera(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_id}")
            
    def stop_camera(self):
        if self.cap is not None:
            self.cap.release()
        if self.show_visualization:
            cv2.destroyAllWindows()
    
    def calculate_face_angles(self, nose, left, right, forward_ratio=0.5):
        center_x = (left[0] + right[0]) / 2
        center_y = (left[1] + right[1]) / 2
        
        face_width = np.sqrt((right[0] - left[0])**2 + (right[1] - left[1])**2)
        nose_deflection_x = (nose[0] - center_x) / face_width
        nose_deflection_y = (nose[1] - center_y) / face_width
        
        max_angle = 45
        x_angle = (nose_deflection_x - forward_ratio) * max_angle * 2 + 40
        y_angle = nose_deflection_y * max_angle * 2
        
        return x_angle, y_angle
        
    def detect_blinks(self, face_landmarks, w, h):
        left_eye_points = [33, 160, 158, 133, 153, 144]
        right_eye_points = [263, 387, 385, 362, 380, 373]
        
        left_eye = [(int(face_landmarks.landmark[p].x * w), int(face_landmarks.landmark[p].y * h)) for p in left_eye_points]
        right_eye = [(int(face_landmarks.landmark[p].x * w), int(face_landmarks.landmark[p].y * h)) for p in right_eye_points]
        
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        
        ear = (left_ear + right_ear) / 2.0

        blinked = False
        
        if ear < self.blink_threshold:
            self.blink_frame_counter += 1
        else:
            if self.blink_frame_counter >= self.blink_duration:
                self.blink_count += 1
                if self.blink_count == 2:
                    blinked = True
                    self.blink_count = 0  # Reset after detection
                    self.blink_frame_counter = 0
                
            self.blink_frame_counter = 0
        
        return blinked


    def get_frame(self):
        if self.cap is None:
            raise RuntimeError("Camera not started. Call start_camera() first.")
            
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            if self.show_visualization:
                cv2.imshow('Face Direction', frame)
                cv2.waitKey(1)
            return None
            
        face_landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        
        nose = (int(face_landmarks.landmark[1].x * w), int(face_landmarks.landmark[1].y * h))
        left = (int(face_landmarks.landmark[234].x * w), int(face_landmarks.landmark[234].y * h))
        right = (int(face_landmarks.landmark[454].x * w), int(face_landmarks.landmark[454].y * h))
        
        x_angle, y_angle = self.calculate_face_angles(nose, left, right)
        self.kalman_x.correct(np.array([[np.float32(x_angle)]]))
        self.kalman_y.correct(np.array([[np.float32(y_angle)]]))
        
        smooth_x = float(self.kalman_x.predict()[0])
        smooth_y = float(self.kalman_y.predict()[0])
        
        blinked = self.detect_blinks(face_landmarks, w, h)
        
        if self.show_visualization:
            cv2.imshow('Face Direction', frame)
            cv2.waitKey(1)
        
        return smooth_x, smooth_y, blinked
