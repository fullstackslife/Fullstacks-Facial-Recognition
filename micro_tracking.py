import cv2
import numpy as np
from collections import deque
import time

class MicroExpressionTracker:
    def __init__(self):
        self.eye_movement_history = {}  # Track eye positions over time
        self.mouth_movement_history = {}  # Track mouth positions over time
        self.expression_change_history = {}  # Track rapid expression changes
        self.micro_expression_threshold = 0.3  # Threshold for micro-expressions
        self.movement_window = 10  # Frames to analyze for movement
        
    def track_eye_movements(self, landmarks, face_box, face_id, frame_time):
        """Track detailed eye movements and gaze patterns"""
        if not landmarks or 'left_eye' not in landmarks:
            return None
        
        if face_id not in self.eye_movement_history:
            self.eye_movement_history[face_id] = {
                'positions': deque(maxlen=30),  # Last 30 positions
                'movements': deque(maxlen=20),  # Movement vectors
                'saccades': [],  # Rapid eye movements
                'fixations': [],  # Stable gaze points
                'total_distance': 0,
                'average_speed': 0
            }
        
        history = self.eye_movement_history[face_id]
        
        # Calculate eye center
        left_eye = landmarks.get('left_eye', (0, 0))
        right_eye = landmarks.get('right_eye', (0, 0))
        eye_center = (
            (left_eye[0] + right_eye[0]) / 2,
            (left_eye[1] + right_eye[1]) / 2
        )
        
        # Store position with timestamp
        current_pos = {
            'x': eye_center[0],
            'y': eye_center[1],
            'time': frame_time,
            'left_eye': left_eye,
            'right_eye': right_eye
        }
        
        # Calculate movement if we have previous position
        if len(history['positions']) > 0:
            prev_pos = history['positions'][-1]
            
            # Calculate movement vector
            dx = eye_center[0] - prev_pos['x']
            dy = eye_center[1] - prev_pos['y']
            dt = frame_time - prev_pos['time']
            
            distance = np.sqrt(dx**2 + dy**2)
            speed = distance / dt if dt > 0 else 0
            
            movement = {
                'dx': dx,
                'dy': dy,
                'distance': distance,
                'speed': speed,
                'angle': np.degrees(np.arctan2(dy, dx)) if dx != 0 else 0,
                'time': frame_time
            }
            
            history['movements'].append(movement)
            history['total_distance'] += distance
            
            # Detect saccades (rapid eye movements)
            if speed > 5:  # Pixels per frame threshold
                history['saccades'].append({
                    'time': frame_time,
                    'speed': speed,
                    'direction': movement['angle']
                })
                # Keep only recent saccades
                if len(history['saccades']) > 50:
                    history['saccades'] = history['saccades'][-50:]
            
            # Detect fixations (stable gaze)
            if speed < 1 and len(history['movements']) >= 5:
                recent_speeds = [m['speed'] for m in list(history['movements'])[-5:]]
                if all(s < 1 for s in recent_speeds):
                    history['fixations'].append({
                        'x': eye_center[0],
                        'y': eye_center[1],
                        'time': frame_time
                    })
                    # Keep only recent fixations
                    if len(history['fixations']) > 20:
                        history['fixations'] = history['fixations'][-20:]
        
        history['positions'].append(current_pos)
        
        # Calculate average speed
        if len(history['movements']) > 0:
            recent_speeds = [m['speed'] for m in list(history['movements'])[-10:]]
            history['average_speed'] = np.mean(recent_speeds) if recent_speeds else 0
        
        # Determine movement pattern
        movement_pattern = self.analyze_eye_pattern(history)
        
        return {
            'current_position': eye_center,
            'movement_speed': history['average_speed'],
            'total_distance': history['total_distance'],
            'saccade_count': len(history['saccades']),
            'fixation_count': len(history['fixations']),
            'recent_saccades': history['saccades'][-5:] if history['saccades'] else [],
            'movement_pattern': movement_pattern,
            'is_moving': history['average_speed'] > 2
        }
    
    def analyze_eye_pattern(self, history):
        """Analyze eye movement patterns"""
        if len(history['movements']) < 5:
            return 'Stable'
        
        recent_movements = list(history['movements'])[-10:]
        speeds = [m['speed'] for m in recent_movements]
        angles = [m['angle'] for m in recent_movements]
        
        avg_speed = np.mean(speeds)
        
        if avg_speed < 1:
            return 'Fixed Gaze'
        elif avg_speed < 3:
            return 'Slow Tracking'
        elif avg_speed < 8:
            return 'Active Scanning'
        else:
            return 'Rapid Movement'
    
    def track_mouth_movements(self, landmarks, face_box, face_id, frame_time):
        """Track detailed mouth movements and shapes"""
        if not landmarks or 'mouth_center' not in landmarks:
            return None
        
        if face_id not in self.mouth_movement_history:
            self.mouth_movement_history[face_id] = {
                'positions': deque(maxlen=30),
                'shapes': deque(maxlen=30),
                'openings': deque(maxlen=30),
                'movements': deque(maxlen=20),
                'total_movement': 0
            }
        
        history = self.mouth_movement_history[face_id]
        
        mouth_center = landmarks.get('mouth_center', (0, 0))
        mouth_left = landmarks.get('mouth_left', (0, 0))
        mouth_right = landmarks.get('mouth_right', (0, 0))
        
        # Calculate mouth width and opening
        mouth_width = np.sqrt(
            (mouth_right[0] - mouth_left[0])**2 + 
            (mouth_right[1] - mouth_left[1])**2
        )
        
        # Estimate mouth opening (vertical distance from center)
        face_height = face_box[3]
        mouth_opening_ratio = mouth_width / face_height if face_height > 0 else 0
        
        current_state = {
            'center': mouth_center,
            'width': mouth_width,
            'opening_ratio': mouth_opening_ratio,
            'time': frame_time,
            'left': mouth_left,
            'right': mouth_right
        }
        
        # Calculate movement
        if len(history['positions']) > 0:
            prev_state = history['positions'][-1]
            
            dx = mouth_center[0] - prev_state['center'][0]
            dy = mouth_center[1] - prev_state['center'][1]
            dt = frame_time - prev_state['time']
            
            distance = np.sqrt(dx**2 + dy**2)
            speed = distance / dt if dt > 0 else 0
            
            # Detect opening/closing
            opening_change = mouth_opening_ratio - prev_state['opening_ratio']
            
            movement = {
                'dx': dx,
                'dy': dy,
                'distance': distance,
                'speed': speed,
                'opening_change': opening_change,
                'time': frame_time
            }
            
            history['movements'].append(movement)
            history['total_movement'] += distance
        
        history['positions'].append(current_state)
        history['shapes'].append({
            'width': mouth_width,
            'opening': mouth_opening_ratio,
            'time': frame_time
        })
        history['openings'].append(mouth_opening_ratio)
        
        # Analyze mouth state
        mouth_state = self.analyze_mouth_state(history)
        
        # Calculate average opening
        avg_opening = np.mean(list(history['openings'])[-10:]) if history['openings'] else 0
        
        return {
            'current_position': mouth_center,
            'width': mouth_width,
            'opening_ratio': mouth_opening_ratio,
            'average_opening': avg_opening,
            'movement_speed': np.mean([m['speed'] for m in list(history['movements'])[-10:]]) if history['movements'] else 0,
            'total_movement': history['total_movement'],
            'state': mouth_state,
            'is_moving': len(history['movements']) > 0 and history['movements'][-1]['speed'] > 2
        }
    
    def analyze_mouth_state(self, history):
        """Analyze current mouth state"""
        if not history['openings']:
            return 'Unknown'
        
        recent_openings = list(history['openings'])[-5:]
        current_opening = recent_openings[-1] if recent_openings else 0
        
        if current_opening < 0.15:
            return 'Closed'
        elif current_opening < 0.25:
            return 'Slightly Open'
        elif current_opening < 0.35:
            return 'Open'
        elif current_opening < 0.45:
            return 'Wide Open'
        else:
            return 'Very Wide'
    
    def detect_micro_expressions(self, current_expression, current_confidence, 
                                face_id, frame_time):
        """Detect micro-expressions (brief, involuntary expressions)"""
        if face_id not in self.expression_change_history:
            self.expression_change_history[face_id] = {
                'expressions': deque(maxlen=20),
                'micro_expressions': [],
                'last_expression': None,
                'last_change_time': frame_time
            }
        
        history = self.expression_change_history[face_id]
        
        # Store current expression
        expr_data = {
            'expression': current_expression,
            'confidence': current_confidence,
            'time': frame_time
        }
        history['expressions'].append(expr_data)
        
        # Detect rapid expression changes (micro-expressions)
        micro_expressions = []
        
        if len(history['expressions']) >= 3:
            recent = list(history['expressions'])[-3:]
            
            # Check for brief expression changes
            if recent[0]['expression'] != recent[1]['expression']:
                # Expression changed
                change_duration = recent[1]['time'] - recent[0]['time']
                
                # If it changed back quickly, it might be a micro-expression
                if len(recent) >= 3 and recent[2]['expression'] == recent[0]['expression']:
                    if change_duration < 0.5:  # Less than 500ms
                        micro_expr = {
                            'expression': recent[1]['expression'],
                            'duration': change_duration,
                            'time': recent[1]['time'],
                            'confidence': recent[1]['confidence']
                        }
                        history['micro_expressions'].append(micro_expr)
                        micro_expressions.append(micro_expr)
                        
                        # Keep only recent micro-expressions
                        if len(history['micro_expressions']) > 30:
                            history['micro_expressions'] = history['micro_expressions'][-30:]
        
        # Analyze micro-expression patterns
        pattern = self.analyze_micro_pattern(history)
        
        return {
            'detected': len(micro_expressions) > 0,
            'recent_micro_expressions': history['micro_expressions'][-5:] if history['micro_expressions'] else [],
            'total_count': len(history['micro_expressions']),
            'pattern': pattern,
            'current_expression': current_expression,
            'expression_stability': self.calculate_stability(history)
        }
    
    def analyze_micro_pattern(self, history):
        """Analyze patterns in micro-expressions"""
        if not history['micro_expressions']:
            return 'No micro-expressions detected'
        
        recent = history['micro_expressions'][-10:] if len(history['micro_expressions']) >= 10 else history['micro_expressions']
        
        if len(recent) == 0:
            return 'Stable expression'
        
        # Count expression types
        expr_counts = {}
        for me in recent:
            expr = me['expression']
            expr_counts[expr] = expr_counts.get(expr, 0) + 1
        
        most_common = max(expr_counts.items(), key=lambda x: x[1]) if expr_counts else None
        
        if most_common and most_common[1] >= 3:
            return f'Frequent {most_common[0]} micro-expressions'
        elif len(recent) >= 5:
            return 'Multiple micro-expressions detected'
        else:
            return 'Occasional micro-expressions'
    
    def calculate_stability(self, history):
        """Calculate expression stability score"""
        if len(history['expressions']) < 5:
            return 1.0
        
        recent = list(history['expressions'])[-10:]
        expressions = [e['expression'] for e in recent]
        
        # Count unique expressions
        unique_count = len(set(expressions))
        total_count = len(expressions)
        
        # Stability is inverse of variation
        stability = 1.0 - (unique_count / total_count) if total_count > 0 else 1.0
        
        return round(stability, 2)
    
    def get_movement_trajectory(self, face_id, feature_type='eye'):
        """Get movement trajectory for visualization"""
        if feature_type == 'eye':
            history = self.eye_movement_history.get(face_id, {})
            positions = history.get('positions', [])
        else:
            history = self.mouth_movement_history.get(face_id, {})
            positions = history.get('positions', [])
        
        if not positions:
            return []
        
        return [(p['x'], p['y']) for p in list(positions)[-20:]]  # Last 20 positions
    
    def reset_tracking(self, face_id):
        """Reset tracking for a face"""
        if face_id in self.eye_movement_history:
            del self.eye_movement_history[face_id]
        if face_id in self.mouth_movement_history:
            del self.mouth_movement_history[face_id]
        if face_id in self.expression_change_history:
            del self.expression_change_history[face_id]


