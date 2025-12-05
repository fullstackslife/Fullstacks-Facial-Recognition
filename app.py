"""
Real-time Face Detection & Analysis Web Application
Flask backend with OpenCV and MediaPipe for facial analysis
"""
import cv2
import numpy as np
import mediapipe as mp
from flask import Flask, render_template, Response, jsonify
import base64
import json

app = Flask(__name__)

# Initialize MediaPipe Face Mesh and Face Detection
mp_face_mesh = mp.solutions.face_mesh
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Global variables for face analysis
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=5,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
face_detection = mp_face_detection.FaceDetection(
    min_detection_confidence=0.5
)


class FaceAnalyzer:
    """Analyze facial features including expressions, blinks, and head pose"""
    
    def __init__(self):
        self.prev_left_eye_ratio = None
        self.prev_right_eye_ratio = None
        self.blink_counter = 0
        self.EYE_AR_THRESHOLD = 0.21
        
    def calculate_eye_aspect_ratio(self, eye_landmarks):
        """Calculate eye aspect ratio for blink detection"""
        # Vertical eye distances
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        # Horizontal eye distance
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, landmarks, img_width, img_height):
        """Detect eye blinks"""
        # Left eye indices (MediaPipe)
        left_eye_indices = [33, 160, 158, 133, 153, 144]
        # Right eye indices
        right_eye_indices = [362, 385, 387, 263, 373, 380]
        
        try:
            # Extract left eye landmarks
            left_eye = np.array([[landmarks[i].x * img_width, 
                                landmarks[i].y * img_height] 
                               for i in left_eye_indices])
            
            # Extract right eye landmarks
            right_eye = np.array([[landmarks[i].x * img_width, 
                                 landmarks[i].y * img_height] 
                                for i in right_eye_indices])
            
            # Calculate eye aspect ratios
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            
            # Average eye aspect ratio
            ear = (left_ear + right_ear) / 2.0
            
            # Detect blink
            blink_detected = False
            if ear < self.EYE_AR_THRESHOLD:
                if self.prev_left_eye_ratio is not None:
                    if self.prev_left_eye_ratio >= self.EYE_AR_THRESHOLD:
                        self.blink_counter += 1
                        blink_detected = True
            
            self.prev_left_eye_ratio = ear
            
            return blink_detected, self.blink_counter, ear
        except:
            return False, self.blink_counter, 0
    
    def estimate_head_pose(self, landmarks, img_width, img_height):
        """Estimate head pose (pitch, yaw, roll)"""
        # Key facial landmarks for pose estimation
        nose_tip = np.array([landmarks[1].x * img_width, 
                            landmarks[1].y * img_height])
        chin = np.array([landmarks[152].x * img_width, 
                        landmarks[152].y * img_height])
        left_eye = np.array([landmarks[33].x * img_width, 
                            landmarks[33].y * img_height])
        right_eye = np.array([landmarks[263].x * img_width, 
                             landmarks[263].y * img_height])
        left_mouth = np.array([landmarks[61].x * img_width, 
                              landmarks[61].y * img_height])
        right_mouth = np.array([landmarks[291].x * img_width, 
                               landmarks[291].y * img_height])
        
        # Calculate angles
        # Yaw (left-right)
        eye_center = (left_eye + right_eye) / 2
        face_width = np.linalg.norm(right_eye - left_eye)
        nose_offset = nose_tip[0] - eye_center[0]
        yaw = (nose_offset / face_width) * 90 if face_width > 0 else 0
        
        # Pitch (up-down)
        face_height = np.linalg.norm(chin - eye_center)
        vertical_offset = nose_tip[1] - eye_center[1]
        pitch = (vertical_offset / face_height) * 60 if face_height > 0 else 0
        
        # Roll (tilt)
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        roll = np.degrees(np.arctan2(dy, dx))
        
        return {
            'yaw': float(yaw),
            'pitch': float(pitch),
            'roll': float(roll)
        }
    
    def detect_expression(self, landmarks, img_width, img_height):
        """Detect basic facial expressions"""
        # Mouth landmarks
        upper_lip = landmarks[13].y * img_height
        lower_lip = landmarks[14].y * img_height
        mouth_left = landmarks[61].x * img_width
        mouth_right = landmarks[291].x * img_width
        
        # Calculate mouth openness and width
        mouth_height = abs(lower_lip - upper_lip)
        mouth_width = abs(mouth_right - mouth_left)
        
        # Simple expression detection
        expression = "Neutral"
        if mouth_height > mouth_width * 0.3:
            expression = "Surprised/Open Mouth"
        elif mouth_width > img_width * 0.15:
            expression = "Smiling"
        
        return expression


analyzer = FaceAnalyzer()


def process_frame(frame):
    """Process video frame for face detection and analysis"""
    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process with Face Mesh
    results = face_mesh.process(rgb_frame)
    
    face_data = []
    
    if results.multi_face_landmarks:
        for face_idx, face_landmarks in enumerate(results.multi_face_landmarks):
            img_height, img_width = frame.shape[:2]
            
            # Draw face mesh
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )
            
            # Analyze face
            blink_detected, blink_count, ear = analyzer.detect_blink(
                face_landmarks.landmark, img_width, img_height
            )
            
            head_pose = analyzer.estimate_head_pose(
                face_landmarks.landmark, img_width, img_height
            )
            
            expression = analyzer.detect_expression(
                face_landmarks.landmark, img_width, img_height
            )
            
            # Get bounding box
            x_coords = [lm.x * img_width for lm in face_landmarks.landmark]
            y_coords = [lm.y * img_height for lm in face_landmarks.landmark]
            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))
            
            # Draw bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Add text information
            y_offset = y_min - 60
            cv2.putText(frame, f"Face {face_idx + 1}", (x_min, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Expression: {expression}", (x_min, y_offset + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Blinks: {blink_count}", (x_min, y_offset + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if blink_detected:
                cv2.putText(frame, "BLINK!", (x_min, y_offset + 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            face_data.append({
                'face_id': face_idx + 1,
                'expression': expression,
                'blink_count': blink_count,
                'head_pose': head_pose,
                'bounding_box': {
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max
                }
            })
    
    # Add face count
    cv2.putText(frame, f"Faces Detected: {len(face_data)}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return frame, face_data


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route - not used for browser camera"""
    return Response("Browser camera mode - use JavaScript", 
                   mimetype='text/plain')


@app.route('/analyze_frame', methods=['POST'])
def analyze_frame():
    """Analyze a single frame from browser camera"""
    from flask import request
    
    try:
        # Get image data from request
        data = request.get_json()
        image_data = data.get('image', '')
        
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Process frame
        processed_frame, face_data = process_frame(frame)
        
        # Encode processed frame back to base64
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'processed_image': f"data:image/jpeg;base64,{processed_image}",
            'face_data': face_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'facial-recognition'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
