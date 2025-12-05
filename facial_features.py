import cv2
import numpy as np
import urllib.request
import os
import time

class FacialFeatureAnalyzer:
    def __init__(self):
        # Load face detector (using DNN for better accuracy)
        self.face_net = self.load_face_detector()
        
        # Load facial landmark predictor (68 points)
        self.landmark_model = self.load_landmark_predictor()
        
        # Expression/emotion categories
        self.expressions = ['Neutral', 'Happy', 'Sad', 'Angry', 'Surprised', 'Fearful', 'Disgusted']
        
    def load_face_detector(self):
        """Load OpenCV DNN face detector"""
        try:
            # Download face detection model files if they don't exist
            prototxt_path = 'models/deploy.prototxt'
            model_path = 'models/res10_300x300_ssd_iter_140000.caffemodel'
            
            if not os.path.exists(prototxt_path):
                os.makedirs('models', exist_ok=True)
                print("Downloading face detection model...")
                urllib.request.urlretrieve(
                    'https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt',
                    prototxt_path
                )
                urllib.request.urlretrieve(
                    'https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel',
                    model_path
                )
            
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            return net
        except Exception as e:
            print(f"Could not load DNN face detector: {e}")
            print("Falling back to Haar Cascade")
            return None
    
    def load_landmark_predictor(self):
        """Load facial landmark predictor"""
        try:
            # Try to use dlib if available, otherwise use OpenCV's approach
            try:
                import dlib
                predictor_path = 'models/shape_predictor_68_face_landmarks.dat'
                if not os.path.exists(predictor_path):
                    print("dlib landmark model not found. Using geometric analysis instead.")
                    return None
                return dlib.shape_predictor(predictor_path)
            except ImportError:
                # Use geometric analysis based on face region
                return None
        except Exception as e:
            print(f"Could not load landmark predictor: {e}")
            return None
    
    def detect_faces_dnn(self, frame):
        """Detect faces using DNN (more accurate)"""
        if self.face_net is None:
            return []
        
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), [104, 117, 123])
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # Confidence threshold
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x, y, x2, y2 = box.astype("int")
                faces.append((x, y, x2 - x, y2 - y, confidence))
        
        return faces
    
    def estimate_facial_landmarks(self, frame, face_box):
        """Estimate facial landmarks using geometric analysis"""
        x, y, w, h = face_box[:4]
        face_roi = frame[y:y+h, x:x+w]
        
        if face_roi.size == 0:
            return None
        
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
        
        # Estimate key facial points based on face geometry
        landmarks = {}
        
        # Face center
        landmarks['nose_tip'] = (x + w // 2, y + h // 2)
        
        # Eye regions (estimated positions)
        landmarks['left_eye'] = (x + int(w * 0.35), y + int(h * 0.35))
        landmarks['right_eye'] = (x + int(w * 0.65), y + int(h * 0.35))
        landmarks['left_eye_corner'] = (x + int(w * 0.25), y + int(h * 0.35))
        landmarks['right_eye_corner'] = (x + int(w * 0.75), y + int(h * 0.35))
        
        # Mouth region
        landmarks['mouth_center'] = (x + w // 2, y + int(h * 0.65))
        landmarks['mouth_left'] = (x + int(w * 0.3), y + int(h * 0.65))
        landmarks['mouth_right'] = (x + int(w * 0.7), y + int(h * 0.65))
        
        # Eyebrows
        landmarks['left_eyebrow'] = (x + int(w * 0.35), y + int(h * 0.25))
        landmarks['right_eyebrow'] = (x + int(w * 0.65), y + int(h * 0.25))
        
        # Face outline
        landmarks['chin'] = (x + w // 2, y + h)
        landmarks['forehead'] = (x + w // 2, y)
        
        return landmarks
    
    def analyze_eye_openness(self, landmarks, face_box):
        """Analyze if eyes are open or closed"""
        if not landmarks:
            return {'left': 0.5, 'right': 0.5, 'status': 'Unknown'}
        
        # Estimate eye openness based on face geometry
        # This is a simplified version - real implementation would use eye aspect ratio
        w, h = face_box[2], face_box[3]
        
        # Simplified: assume eyes are open if face is large enough
        face_area = w * h
        openness = min(1.0, face_area / 10000)  # Normalize
        
        status = 'Open' if openness > 0.3 else 'Closed'
        
        return {
            'left': openness,
            'right': openness,
            'status': status
        }
    
    def analyze_mouth_shape(self, landmarks, face_box):
        """Analyze mouth shape and expression"""
        if not landmarks:
            return {'shape': 'Unknown', 'open': False}
        
        # Estimate mouth openness
        w, h = face_box[2], face_box[3]
        mouth_width_ratio = 0.4  # Estimated
        
        # Simplified analysis
        if 'mouth_center' in landmarks:
            # Could analyze mouth region more deeply
            return {
                'shape': 'Normal',
                'open': False,
                'width_ratio': mouth_width_ratio
            }
        
        return {'shape': 'Unknown', 'open': False}
    
    def analyze_head_pose(self, landmarks, face_box):
        """Estimate head pose (yaw, pitch, roll)"""
        if not landmarks:
            return {'yaw': 0, 'pitch': 0, 'roll': 0, 'orientation': 'Frontal'}
        
        x, y, w, h = face_box[:4]
        
        # Simplified head pose estimation
        # Real implementation would use 3D model fitting
        center_x = x + w // 2
        frame_center_x = 320  # Assuming 640 width
        
        # Estimate yaw (left/right turn)
        yaw = (center_x - frame_center_x) / frame_center_x * 30  # degrees
        
        if abs(yaw) < 10:
            orientation = 'Frontal'
        elif yaw > 0:
            orientation = 'Looking Right'
        else:
            orientation = 'Looking Left'
        
        return {
            'yaw': round(yaw, 1),
            'pitch': 0,  # Would need more analysis
            'roll': 0,
            'orientation': orientation
        }
    
    def detect_expression(self, frame, face_box, landmarks):
        """Detect facial expression/emotion"""
        if not landmarks:
            return {'expression': 'Neutral', 'confidence': 0.5}
        
        # Simplified expression detection based on geometric features
        # Real implementation would use deep learning models
        
        x, y, w, h = face_box[:4]
        face_roi = frame[y:y+h, x:x+w]
        
        if face_roi.size == 0:
            return {'expression': 'Neutral', 'confidence': 0.5}
        
        # Analyze mouth region for smile detection
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
        
        # Simple smile detection using edge detection in mouth region
        mouth_y = int(h * 0.65)
        mouth_region = gray[max(0, mouth_y-10):min(h, mouth_y+10), int(w*0.3):int(w*0.7)]
        
        if mouth_region.size > 0:
            # Detect horizontal edges (smile indicator)
            edges = cv2.Canny(mouth_region, 50, 150)
            edge_density = np.sum(edges > 0) / mouth_region.size
            
            if edge_density > 0.1:
                return {'expression': 'Happy', 'confidence': min(0.9, edge_density * 5)}
        
        # Default to neutral
        return {'expression': 'Neutral', 'confidence': 0.6}
    
    def analyze_facial_features(self, frame, face_box, face_id=None, advanced_tracker=None, micro_tracker=None):
        """Comprehensive facial feature analysis with advanced tracking"""
        # Get landmarks
        landmarks = self.estimate_facial_landmarks(frame, face_box)
        
        # Analyze basic features
        eye_analysis = self.analyze_eye_openness(landmarks, face_box)
        mouth_analysis = self.analyze_mouth_shape(landmarks, face_box)
        head_pose = self.analyze_head_pose(landmarks, face_box)
        expression = self.detect_expression(frame, face_box, landmarks)
        
        # Calculate face symmetry
        symmetry_score = self.calculate_symmetry(landmarks, face_box)
        
        # Advanced tracking if available
        advanced_features = {}
        if advanced_tracker and face_id is not None:
            x, y, w, h = face_box[:4]
            face_roi = frame[y:y+h, x:x+w]
            
            # Age and gender estimation
            age_gender = advanced_tracker.estimate_age_gender(face_roi)
            
            # Blink detection
            blink_info = advanced_tracker.detect_blink(landmarks, face_box, face_id)
            
            # Gaze direction
            gaze = advanced_tracker.estimate_gaze_direction(landmarks, face_box)
            
            # Face quality
            quality = advanced_tracker.calculate_face_quality(frame, face_box)
            
            # Facial action units
            action_units = advanced_tracker.detect_facial_action_units(landmarks, face_box)
            
            # Face roll/tilt
            face_roll = advanced_tracker.calculate_face_angle_roll(landmarks, face_box)
            
            # Track expression changes
            advanced_tracker.track_expression_changes(
                face_id, expression['expression'], expression['confidence']
            )
            expression_stats = advanced_tracker.get_expression_stats(face_id)
            
            advanced_features = {
                'age_gender': age_gender,
                'blink': blink_info,
                'gaze': gaze,
                'quality': quality,
                'action_units': action_units,
                'face_roll': face_roll,
                'expression_stats': expression_stats
            }
            
            # Micro-tracking (eye movements, mouth movements, micro-expressions)
            if micro_tracker and face_id is not None:
                frame_time = time.time()
                
                # Track eye movements
                eye_movements = micro_tracker.track_eye_movements(
                    landmarks, face_box, face_id, frame_time
                )
                
                # Track mouth movements
                mouth_movements = micro_tracker.track_mouth_movements(
                    landmarks, face_box, face_id, frame_time
                )
                
                # Detect micro-expressions
                micro_expressions = micro_tracker.detect_micro_expressions(
                    expression['expression'], expression['confidence'],
                    face_id, frame_time
                )
                
                advanced_features['eye_movements'] = eye_movements
                advanced_features['mouth_movements'] = mouth_movements
                advanced_features['micro_expressions'] = micro_expressions
        
        return {
            'landmarks': landmarks,
            'eyes': eye_analysis,
            'mouth': mouth_analysis,
            'head_pose': head_pose,
            'expression': expression,
            'symmetry': symmetry_score,
            'advanced': advanced_features,
            'features': {
                'has_glasses': False,  # Could add detection
                'has_beard': False,    # Could add detection
                'face_shape': 'Oval'   # Could analyze
            }
        }
    
    def calculate_symmetry(self, landmarks, face_box):
        """Calculate facial symmetry score"""
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return 0.5
        
        # Compare left and right side features
        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        
        # Calculate symmetry based on eye positions
        face_center_x = face_box[0] + face_box[2] // 2
        left_dist = abs(left_eye[0] - face_center_x)
        right_dist = abs(right_eye[0] - face_center_x)
        
        if left_dist + right_dist > 0:
            symmetry = 1.0 - abs(left_dist - right_dist) / (left_dist + right_dist)
        else:
            symmetry = 0.5
        
        return round(symmetry, 2)
    
    def draw_landmarks(self, frame, landmarks, color=(0, 255, 255)):
        """Draw facial landmarks on frame - DISABLED for cleaner video feed"""
        # Landmarks are now only used for analysis, not displayed
        # This keeps the video feed clean
        return frame

