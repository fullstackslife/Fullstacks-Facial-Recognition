import cv2
import numpy as np
from collections import deque
import time

class AdvancedFaceTracker:
    def __init__(self):
        self.blink_history = {}  # Track blinks per face
        self.gaze_history = {}   # Track gaze direction
        self.expression_history = {}  # Track expression over time
        self.quality_metrics = {}  # Track face quality
        
    def estimate_age_gender(self, face_roi):
        """Estimate age and gender from face region"""
        # Simplified estimation based on facial features
        # Real implementation would use a trained model
        
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
        
        # Analyze facial features for age estimation
        # This is a simplified heuristic-based approach
        h, w = gray.shape
        
        # Estimate based on face proportions and texture
        # Younger faces tend to have smoother skin, older faces have more texture
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Simplified age estimation (would need ML model for accuracy)
        if laplacian_var < 100:
            age_range = "20-30"
        elif laplacian_var < 200:
            age_range = "30-40"
        elif laplacian_var < 300:
            age_range = "40-50"
        else:
            age_range = "50+"
        
        # Gender estimation based on facial structure (simplified)
        # Real implementation would use deep learning
        face_ratio = h / w if w > 0 else 1.0
        
        # Simplified heuristic (not very accurate without ML)
        if face_ratio > 1.3:
            gender = "Female"
        else:
            gender = "Male"
        
        return {
            'age_range': age_range,
            'gender': gender,
            'confidence': 0.6  # Low confidence for heuristic approach
        }
    
    def detect_blink(self, landmarks, face_box, face_id):
        """Detect eye blinks using Eye Aspect Ratio (EAR)"""
        if not landmarks or 'left_eye' not in landmarks:
            return {'blinked': False, 'ear': 0.3}
        
        # Calculate Eye Aspect Ratio (simplified)
        # Real implementation would use 6 points around each eye
        left_eye = landmarks.get('left_eye', (0, 0))
        right_eye = landmarks.get('right_eye', (0, 0))
        left_corner = landmarks.get('left_eye_corner', (0, 0))
        right_corner = landmarks.get('right_eye_corner', (0, 0))
        
        # Calculate distances
        def distance(p1, p2):
            return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        # Simplified EAR calculation
        vertical_dist = abs(left_eye[1] - left_corner[1])
        horizontal_dist = distance(left_eye, right_eye)
        
        if horizontal_dist > 0:
            ear = vertical_dist / horizontal_dist
        else:
            ear = 0.3
        
        # Blink threshold (simplified)
        blink_threshold = 0.2
        
        # Track blink history
        if face_id not in self.blink_history:
            self.blink_history[face_id] = {
                'ear_history': deque(maxlen=10),
                'blink_count': 0,
                'last_blink_time': 0
            }
        
        history = self.blink_history[face_id]
        history['ear_history'].append(ear)
        
        # Detect blink (EAR drops below threshold)
        blinked = False
        if len(history['ear_history']) >= 3:
            recent_ears = list(history['ear_history'])[-3:]
            if all(e < blink_threshold for e in recent_ears):
                # Check if enough time has passed since last blink
                current_time = time.time()
                if current_time - history['last_blink_time'] > 0.3:  # 300ms debounce
                    history['blink_count'] += 1
                    history['last_blink_time'] = current_time
                    blinked = True
        
        # Note: This is a simplified blink detection
        # The accurate count comes from individual_eyes.synchronized_blink_count
        return {
            'blinked': blinked,
            'ear': round(ear, 3),
            'blink_count': history['blink_count'],  # Legacy - use synchronized_blink_count from individual_eyes instead
            'eyes_closed': ear < blink_threshold,
            'note': 'Use synchronized_blink_count from individual_eyes for accurate count'
        }
    
    def estimate_gaze_direction(self, landmarks, face_box):
        """Estimate gaze direction based on eye position"""
        if not landmarks:
            return {'direction': 'Center', 'angle': 0}
        
        left_eye = landmarks.get('left_eye', (0, 0))
        right_eye = landmarks.get('right_eye', (0, 0))
        
        # Calculate eye center
        eye_center_x = (left_eye[0] + right_eye[0]) / 2
        face_center_x = face_box[0] + face_box[2] / 2
        
        # Calculate offset
        offset = eye_center_x - face_center_x
        offset_ratio = offset / (face_box[2] / 2) if face_box[2] > 0 else 0
        
        # Determine gaze direction
        if abs(offset_ratio) < 0.1:
            direction = 'Center'
        elif offset_ratio > 0.2:
            direction = 'Looking Right'
        elif offset_ratio < -0.2:
            direction = 'Looking Left'
        else:
            direction = 'Slightly ' + ('Right' if offset_ratio > 0 else 'Left')
        
        return {
            'direction': direction,
            'angle': round(offset_ratio * 30, 1),  # Approximate angle
            'offset_ratio': round(offset_ratio, 2)
        }
    
    def calculate_face_quality(self, frame, face_box):
        """Calculate face image quality metrics"""
        x, y, w, h = face_box[:4]
        face_roi = frame[y:y+h, x:x+w]
        
        if face_roi.size == 0:
            return {'quality': 'Poor', 'score': 0}
        
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
        
        # Calculate various quality metrics
        # 1. Sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 2. Brightness
        brightness = np.mean(gray)
        
        # 3. Contrast
        contrast = gray.std()
        
        # 4. Face size (larger is better for analysis)
        face_area = w * h
        frame_area = frame.shape[0] * frame.shape[1]
        size_ratio = face_area / frame_area if frame_area > 0 else 0
        
        # Normalize scores (0-1)
        sharpness_score = min(1.0, sharpness / 500)
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal around 127
        contrast_score = min(1.0, contrast / 50)
        size_score = min(1.0, size_ratio * 10)
        
        # Overall quality score
        quality_score = (sharpness_score * 0.3 + brightness_score * 0.2 + 
                        contrast_score * 0.2 + size_score * 0.3)
        
        # Categorize quality
        if quality_score > 0.7:
            quality = 'Excellent'
        elif quality_score > 0.5:
            quality = 'Good'
        elif quality_score > 0.3:
            quality = 'Fair'
        else:
            quality = 'Poor'
        
        return {
            'quality': quality,
            'score': round(quality_score, 2),
            'sharpness': round(sharpness, 1),
            'brightness': round(brightness, 1),
            'contrast': round(contrast, 1),
            'size_ratio': round(size_ratio * 100, 1)
        }
    
    def detect_facial_action_units(self, landmarks, face_box):
        """Detect Facial Action Units (simplified FACS)"""
        if not landmarks:
            return {}
        
        action_units = {}
        
        # AU1 - Inner Brow Raiser (simplified)
        if 'left_eyebrow' in landmarks and 'forehead' in landmarks:
            brow_height = abs(landmarks['left_eyebrow'][1] - landmarks['forehead'][1])
            face_height = face_box[3]
            if brow_height / face_height > 0.15:
                action_units['AU1'] = True  # Inner brow raised
        
        # AU4 - Brow Lowerer
        if 'left_eyebrow' in landmarks and 'left_eye' in landmarks:
            brow_eye_dist = abs(landmarks['left_eyebrow'][1] - landmarks['left_eye'][1])
            face_height = face_box[3]
            if brow_eye_dist / face_height < 0.08:
                action_units['AU4'] = True  # Brows lowered
        
        # AU12 - Lip Corner Puller (smile)
        if 'mouth_center' in landmarks and 'mouth_left' in landmarks:
            mouth_width = abs(landmarks['mouth_left'][0] - landmarks['mouth_right'][0])
            face_width = face_box[2]
            if mouth_width / face_width > 0.4:
                action_units['AU12'] = True  # Smile detected
        
        # AU25 - Lips Part (mouth open)
        # Simplified - would need more landmarks for accuracy
        
        return action_units
    
    def calculate_face_angle_roll(self, landmarks, face_box):
        """Calculate face roll (rotation around Z-axis)"""
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return {'roll': 0, 'tilt': 'Straight'}
        
        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        
        # Calculate angle between eyes
        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        
        if dx != 0:
            roll_angle = np.degrees(np.arctan2(dy, dx))
        else:
            roll_angle = 0
        
        # Categorize tilt
        if abs(roll_angle) < 5:
            tilt = 'Straight'
        elif roll_angle > 5:
            tilt = 'Tilted Right'
        else:
            tilt = 'Tilted Left'
        
        return {
            'roll': round(roll_angle, 1),
            'tilt': tilt
        }
    
    def track_expression_changes(self, face_id, expression, confidence):
        """Track expression changes over time"""
        if face_id not in self.expression_history:
            self.expression_history[face_id] = {
                'current': expression,
                'confidence': confidence,
                'duration': 0,
                'changes': 0,
                'last_change_time': time.time()
            }
            return
        
        history = self.expression_history[face_id]
        
        if history['current'] != expression:
            history['changes'] += 1
            history['last_change_time'] = time.time()
            history['current'] = expression
            history['confidence'] = confidence
            history['duration'] = 0
        else:
            history['duration'] = time.time() - history['last_change_time']
            history['confidence'] = max(history['confidence'], confidence)
    
    def get_expression_stats(self, face_id):
        """Get expression statistics for a face"""
        if face_id not in self.expression_history:
            return None
        
        return self.expression_history[face_id]
    
    def reset_face_tracking(self, face_id):
        """Reset tracking for a specific face"""
        if face_id in self.blink_history:
            del self.blink_history[face_id]
        if face_id in self.gaze_history:
            del self.gaze_history[face_id]
        if face_id in self.expression_history:
            del self.expression_history[face_id]
        if face_id in self.quality_metrics:
            del self.quality_metrics[face_id]

