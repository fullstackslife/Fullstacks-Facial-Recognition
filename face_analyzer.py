import cv2
import numpy as np
from collections import defaultdict
import time

class FaceAnalyzer:
    def __init__(self):
        # Load face detection cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Face tracking
        self.face_tracks = {}  # Track faces across frames
        self.next_face_id = 0
        self.track_history = defaultdict(list)  # Store position history
        
        # Statistics
        self.stats = {
            'total_faces_detected': 0,
            'unique_faces_seen': 0,
            'max_faces_simultaneous': 0,
            'session_start': time.time()
        }
        
    def calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU) of two bounding boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0
        
        inter_area = (xi2 - xi1) * (yi2 - yi1)
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0
    
    def track_faces(self, faces):
        """Track faces across frames and assign IDs"""
        current_frame_ids = {}
        
        # Match current faces with existing tracks
        for face in faces:
            x, y, w, h = face
            center = (x + w // 2, y + h // 2)
            
            best_match_id = None
            best_iou = 0.3  # Minimum IoU threshold
            
            # Find best matching track
            for face_id, last_box in self.face_tracks.items():
                iou = self.calculate_iou(face, last_box)
                if iou > best_iou:
                    best_iou = iou
                    best_match_id = face_id
            
            # Assign ID
            if best_match_id is not None:
                face_id = best_match_id
            else:
                # New face
                face_id = self.next_face_id
                self.next_face_id += 1
                self.stats['unique_faces_seen'] = max(self.stats['unique_faces_seen'], self.next_face_id)
            
            self.face_tracks[face_id] = face
            current_frame_ids[face_id] = {
                'box': face,
                'center': center,
                'area': w * h,
                'size': (w, h)
            }
            
            # Update track history
            self.track_history[face_id].append({
                'center': center,
                'time': time.time(),
                'area': w * h
            })
            
            # Keep only recent history (last 30 positions)
            if len(self.track_history[face_id]) > 30:
                self.track_history[face_id] = self.track_history[face_id][-30:]
        
        # Remove old tracks (faces that disappeared)
        disappeared_ids = set(self.face_tracks.keys()) - set(current_frame_ids.keys())
        for face_id in disappeared_ids:
            # Keep track for a bit in case face reappears
            if face_id in self.face_tracks:
                del self.face_tracks[face_id]
        
        return current_frame_ids
    
    def analyze_faces(self, frame):
        """Detect and analyze faces in a frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Update statistics
        self.stats['total_faces_detected'] += len(faces)
        self.stats['max_faces_simultaneous'] = max(
            self.stats['max_faces_simultaneous'], 
            len(faces)
        )
        
        # Track faces
        tracked_faces = self.track_faces(faces)
        
        # Calculate additional metrics
        analysis = {
            'faces': tracked_faces,
            'count': len(faces),
            'frame_width': frame.shape[1],
            'frame_height': frame.shape[0]
        }
        
        return analysis
    
    def get_face_position_percentage(self, center, frame_width, frame_height):
        """Get face position as percentage of frame"""
        x_percent = (center[0] / frame_width) * 100
        y_percent = (center[1] / frame_height) * 100
        return (x_percent, y_percent)
    
    def get_face_size_category(self, area, frame_area):
        """Categorize face size (close, medium, far)"""
        size_percent = (area / frame_area) * 100
        if size_percent > 5:
            return "Close"
        elif size_percent > 2:
            return "Medium"
        else:
            return "Far"
    
    def calculate_movement_speed(self, face_id):
        """Calculate movement speed of a face"""
        history = self.track_history.get(face_id, [])
        if len(history) < 2:
            return 0
        
        # Calculate average speed over last few positions
        speeds = []
        for i in range(1, min(len(history), 5)):
            prev = history[i-1]
            curr = history[i]
            
            dx = curr['center'][0] - prev['center'][0]
            dy = curr['center'][1] - prev['center'][1]
            dt = curr['time'] - prev['time']
            
            if dt > 0:
                speed = np.sqrt(dx**2 + dy**2) / dt
                speeds.append(speed)
        
        return np.mean(speeds) if speeds else 0
    
    def get_statistics(self):
        """Get overall statistics"""
        session_duration = time.time() - self.stats['session_start']
        return {
            **self.stats,
            'session_duration': session_duration,
            'avg_faces_per_second': self.stats['total_faces_detected'] / session_duration if session_duration > 0 else 0
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'total_faces_detected': 0,
            'unique_faces_seen': 0,
            'max_faces_simultaneous': 0,
            'session_start': time.time()
        }
        self.face_tracks = {}
        self.track_history = defaultdict(list)
        self.next_face_id = 0

    def reset_session(self):
        """Alias for reset_statistics for compatibility"""
        self.reset_statistics()

