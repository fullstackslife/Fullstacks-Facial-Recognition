import cv2
import numpy as np
import math

class QuadrantTracker:
    def __init__(self):
        pass
    
    def divide_face_quadrants(self, face_box, landmarks):
        """Divide face into 4 quadrants and analyze each"""
        if not landmarks:
            return None
        
        x, y, w, h = face_box[:4]
        center_x = x + w // 2
        center_y = y + h // 2
        
        quadrants = {
            'top_left': {
                'bounds': (x, y, center_x - x, center_y - y),
                'center': (x + (center_x - x) // 2, y + (center_y - y) // 2),
                'features': []
            },
            'top_right': {
                'bounds': (center_x, y, x + w - center_x, center_y - y),
                'center': (center_x + (x + w - center_x) // 2, y + (center_y - y) // 2),
                'features': []
            },
            'bottom_left': {
                'bounds': (x, center_y, center_x - x, y + h - center_y),
                'center': (x + (center_x - x) // 2, center_y + (y + h - center_y) // 2),
                'features': []
            },
            'bottom_right': {
                'bounds': (center_x, center_y, x + w - center_x, y + h - center_y),
                'center': (center_x + (x + w - center_x) // 2, center_y + (y + h - center_y) // 2),
                'features': []
            }
        }
        
        # Map landmarks to quadrants
        for name, point in landmarks.items():
            px, py = point
            if px < center_x and py < center_y:
                quadrants['top_left']['features'].append(name)
            elif px >= center_x and py < center_y:
                quadrants['top_right']['features'].append(name)
            elif px < center_x and py >= center_y:
                quadrants['bottom_left']['features'].append(name)
            else:
                quadrants['bottom_right']['features'].append(name)
        
        return quadrants
    
    def analyze_quadrant_movement(self, quadrants, prev_quadrants):
        """Analyze movement in each quadrant"""
        if not prev_quadrants:
            return {q: {'movement': 0, 'stability': 1.0} for q in quadrants.keys()}
        
        quadrant_analysis = {}
        for q_name in quadrants.keys():
            if q_name in prev_quadrants:
                curr_center = quadrants[q_name]['center']
                prev_center = prev_quadrants[q_name]['center']
                
                dx = curr_center[0] - prev_center[0]
                dy = curr_center[1] - prev_center[1]
                movement = math.sqrt(dx**2 + dy**2)
                
                # Stability is inverse of movement
                stability = max(0, 1.0 - (movement / 50))  # Normalize
                
                quadrant_analysis[q_name] = {
                    'movement': movement,
                    'stability': stability,
                    'direction': self.get_direction(dx, dy)
                }
            else:
                quadrant_analysis[q_name] = {
                    'movement': 0,
                    'stability': 1.0,
                    'direction': 'None'
                }
        
        return quadrant_analysis
    
    def get_direction(self, dx, dy):
        """Get movement direction"""
        if abs(dx) < 2 and abs(dy) < 2:
            return 'Stable'
        
        angle = math.degrees(math.atan2(dy, dx))
        
        if -22.5 <= angle < 22.5:
            return 'Right'
        elif 22.5 <= angle < 67.5:
            return 'Down-Right'
        elif 67.5 <= angle < 112.5:
            return 'Down'
        elif 112.5 <= angle < 157.5:
            return 'Down-Left'
        elif 157.5 <= angle or angle < -157.5:
            return 'Left'
        elif -157.5 <= angle < -112.5:
            return 'Up-Left'
        elif -112.5 <= angle < -67.5:
            return 'Up'
        else:
            return 'Up-Right'

class EyeTracker:
    def __init__(self):
        self.eye_history = {}  # Track each eye separately
    
    def track_individual_eyes(self, landmarks, face_box, face_id, frame_time):
        """Track left and right eyes separately with detailed metrics"""
        if not landmarks or 'left_eye' not in landmarks:
            return None
        
        if face_id not in self.eye_history:
            self.eye_history[face_id] = {
                'left': {'positions': [], 'openness_history': []},
                'right': {'positions': [], 'openness_history': []}
            }
        
        history = self.eye_history[face_id]
        
        left_eye = landmarks.get('left_eye', (0, 0))
        right_eye = landmarks.get('right_eye', (0, 0))
        left_corner = landmarks.get('left_eye_corner', (0, 0))
        right_corner = landmarks.get('right_eye_corner', (0, 0))
        
        # Calculate Eye Aspect Ratio (EAR) for each eye
        def calculate_ear(eye_center, corner):
            # Simplified EAR - distance from center to corner
            vertical = abs(eye_center[1] - corner[1])
            horizontal = abs(eye_center[0] - corner[0])
            if horizontal > 0:
                return vertical / horizontal
            return 0.3
        
        left_ear = calculate_ear(left_eye, left_corner)
        right_ear = calculate_ear(right_eye, right_corner)
        
        # Determine open/closed state
        blink_threshold = 0.2
        left_open = left_ear > blink_threshold
        right_open = right_ear > blink_threshold
        
        # Track positions
        history['left']['positions'].append({
            'position': left_eye,
            'ear': left_ear,
            'open': left_open,
            'time': frame_time
        })
        history['right']['positions'].append({
            'position': right_eye,
            'ear': right_ear,
            'open': right_open,
            'time': frame_time
        })
        
        # Keep only recent history
        if len(history['left']['positions']) > 30:
            history['left']['positions'] = history['left']['positions'][-30:]
        if len(history['right']['positions']) > 30:
            history['right']['positions'] = history['right']['positions'][-30:]
        
        # Calculate movement for each eye
        left_movement = self.calculate_eye_movement(history['left']['positions'])
        right_movement = self.calculate_eye_movement(history['right']['positions'])
        
        # Detect blinks for each eye (individual)
        left_blinks = self.detect_eye_blinks(history['left']['positions'])
        right_blinks = self.detect_eye_blinks(history['right']['positions'])
        
        # Detect synchronized blinks (real blinks - both eyes together)
        synchronized_blinks = self.detect_synchronized_blinks(
            history['left']['positions'],
            history['right']['positions']
        )
        
        return {
            'left': {
                'position': left_eye,
                'ear': round(left_ear, 3),
                'open': left_open,
                'movement': left_movement,
                'individual_blinks': left_blinks,  # Individual eye blinks
                'status': 'Open' if left_open else 'Closed'
            },
            'right': {
                'position': right_eye,
                'ear': round(right_ear, 3),
                'open': right_open,
                'movement': right_movement,
                'individual_blinks': right_blinks,  # Individual eye blinks
                'status': 'Open' if right_open else 'Closed'
            },
            'synchronized': left_open == right_open,
            'asymmetry': abs(left_ear - right_ear),
            'synchronized_blink_count': synchronized_blinks  # Real blink count
        }
    
    def calculate_eye_movement(self, positions):
        """Calculate eye movement metrics"""
        if len(positions) < 2:
            return {'speed': 0, 'distance': 0, 'direction': 'Stable'}
        
        recent = positions[-5:] if len(positions) >= 5 else positions
        total_distance = 0
        speeds = []
        
        for i in range(1, len(recent)):
            prev = recent[i-1]
            curr = recent[i]
            
            dx = curr['position'][0] - prev['position'][0]
            dy = curr['position'][1] - prev['position'][1]
            dt = curr['time'] - prev['time']
            
            distance = math.sqrt(dx**2 + dy**2)
            total_distance += distance
            
            if dt > 0:
                speed = distance / dt
                speeds.append(speed)
        
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        # Get direction from last movement
        if len(recent) >= 2:
            last = recent[-1]
            prev = recent[-2]
            dx = last['position'][0] - prev['position'][0]
            dy = last['position'][1] - prev['position'][1]
            direction = self.get_movement_direction(dx, dy)
        else:
            direction = 'Stable'
        
        return {
            'speed': round(avg_speed, 2),
            'total_distance': round(total_distance, 2),
            'direction': direction
        }
    
    def detect_eye_blinks(self, positions):
        """Count blinks for an eye - only counts complete close-open cycles"""
        if len(positions) < 3:
            return 0
        
        blink_count = 0
        in_blink = False
        blink_start_time = None
        
        for i in range(1, len(positions)):
            current = positions[i]
            previous = positions[i-1]
            
            # Eye just closed
            if not current['open'] and previous['open']:
                in_blink = True
                blink_start_time = current['time']
            # Eye just opened after being closed - complete blink
            elif current['open'] and in_blink:
                # Only count if blink duration is reasonable (50ms to 500ms)
                if blink_start_time:
                    blink_duration = current['time'] - blink_start_time
                    if 0.05 <= blink_duration <= 0.5:  # Valid blink duration
                        blink_count += 1
                in_blink = False
                blink_start_time = None
        
        return blink_count
    
    def detect_synchronized_blinks(self, left_positions, right_positions):
        """Detect synchronized blinks (both eyes close together) - this is the real blink count"""
        if len(left_positions) < 3 or len(right_positions) < 3:
            return 0
        
        synchronized_blinks = 0
        left_in_blink = False
        right_in_blink = False
        left_blink_start = None
        right_blink_start = None
        
        # Find minimum length
        min_len = min(len(left_positions), len(right_positions))
        
        for i in range(1, min_len):
            left_curr = left_positions[i]
            left_prev = left_positions[i-1]
            right_curr = right_positions[i]
            right_prev = right_positions[i-1]
            
            # Left eye blink detection
            if not left_curr['open'] and left_prev['open']:
                left_in_blink = True
                left_blink_start = left_curr['time']
            elif left_curr['open'] and left_in_blink:
                left_in_blink = False
                if left_blink_start:
                    left_blink_duration = left_curr['time'] - left_blink_start
                    # Reset if blink was too long (not a real blink)
                    if left_blink_duration > 0.5:
                        left_blink_start = None
            
            # Right eye blink detection
            if not right_curr['open'] and right_prev['open']:
                right_in_blink = True
                right_blink_start = right_curr['time']
            elif right_curr['open'] and right_in_blink:
                right_in_blink = False
                if right_blink_start:
                    right_blink_duration = right_curr['time'] - right_blink_start
                    # Reset if blink was too long (not a real blink)
                    if right_blink_duration > 0.5:
                        right_blink_start = None
            
            # Check for synchronized blink (both eyes closed at similar times)
            if left_blink_start and right_blink_start:
                time_diff = abs(left_blink_start - right_blink_start)
                # If both eyes closed within 100ms of each other, it's a synchronized blink
                if time_diff <= 0.1:
                    # Check if both completed the blink
                    if not left_in_blink and not right_in_blink:
                        # Verify both blinks were valid duration
                        left_duration = left_positions[i]['time'] - left_blink_start if i < len(left_positions) else 0
                        right_duration = right_positions[i]['time'] - right_blink_start if i < len(right_positions) else 0
                        
                        if 0.05 <= left_duration <= 0.5 and 0.05 <= right_duration <= 0.5:
                            synchronized_blinks += 1
                            left_blink_start = None
                            right_blink_start = None
        
        return synchronized_blinks
    
    def get_movement_direction(self, dx, dy):
        """Get movement direction"""
        if abs(dx) < 1 and abs(dy) < 1:
            return 'Stable'
        
        angle = math.degrees(math.atan2(dy, dx))
        
        if -22.5 <= angle < 22.5:
            return 'Right'
        elif 22.5 <= angle < 67.5:
            return 'Down-Right'
        elif 67.5 <= angle < 112.5:
            return 'Down'
        elif 112.5 <= angle < 157.5:
            return 'Down-Left'
        elif 157.5 <= angle or angle < -157.5:
            return 'Left'
        elif -157.5 <= angle < -112.5:
            return 'Up-Left'
        elif -112.5 <= angle < -67.5:
            return 'Up'
        else:
            return 'Up-Right'

class HeadPoseTracker:
    def __init__(self):
        pass
    
    def calculate_full_head_pose(self, landmarks, face_box):
        """Calculate complete 3D head pose (pitch, yaw, roll)"""
        if not landmarks:
            return {'pitch': 0, 'yaw': 0, 'roll': 0, 'orientation': 'Frontal'}
        
        x, y, w, h = face_box[:4]
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Roll (rotation around Z-axis) - from eye alignment
        if 'left_eye' in landmarks and 'right_eye' in landmarks:
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            
            dy = right_eye[1] - left_eye[1]
            dx = right_eye[0] - left_eye[0]
            
            if dx != 0:
                roll = math.degrees(math.atan2(dy, dx))
            else:
                roll = 0
        else:
            roll = 0
        
        # Yaw (rotation around Y-axis) - left/right turn
        if 'left_eye' in landmarks and 'right_eye' in landmarks:
            eye_center_x = (landmarks['left_eye'][0] + landmarks['right_eye'][0]) / 2
            offset = eye_center_x - face_center_x
            offset_ratio = offset / (w / 2) if w > 0 else 0
            yaw = offset_ratio * 30  # Approximate degrees
        else:
            yaw = 0
        
        # Pitch (rotation around X-axis) - up/down tilt
        if 'nose_tip' in landmarks and 'forehead' in landmarks:
            nose = landmarks['nose_tip']
            forehead = landmarks['forehead']
            
            vertical_offset = nose[1] - forehead[1]
            face_height = h
            pitch_ratio = vertical_offset / face_height if face_height > 0 else 0
            
            # Normalize pitch (0 = looking straight, positive = looking up, negative = looking down)
            pitch = (pitch_ratio - 0.5) * 40  # Approximate degrees
        else:
            pitch = 0
        
        # Determine overall orientation
        orientation = self.determine_orientation(pitch, yaw, roll)
        
        return {
            'pitch': round(pitch, 1),  # Up/Down
            'yaw': round(yaw, 1),      # Left/Right
            'roll': round(roll, 1),     # Tilt
            'orientation': orientation,
            'pitch_direction': 'Up' if pitch > 5 else ('Down' if pitch < -5 else 'Level'),
            'yaw_direction': 'Right' if yaw > 10 else ('Left' if yaw < -10 else 'Center'),
            'roll_direction': 'Right' if roll > 5 else ('Left' if roll < -5 else 'Straight')
        }
    
    def determine_orientation(self, pitch, yaw, roll):
        """Determine overall head orientation"""
        if abs(pitch) < 10 and abs(yaw) < 10 and abs(roll) < 5:
            return 'Frontal'
        
        parts = []
        if pitch > 10:
            parts.append('Looking Up')
        elif pitch < -10:
            parts.append('Looking Down')
        
        if yaw > 10:
            parts.append('Right')
        elif yaw < -10:
            parts.append('Left')
        
        if roll > 5:
            parts.append('Tilted Right')
        elif roll < -5:
            parts.append('Tilted Left')
        
        return ' '.join(parts) if parts else 'Frontal'


