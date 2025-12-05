from flask import Flask, render_template, Response, jsonify, request
import threading
import numpy as np
from collections import deque
import time
import base64
import sys
import os

app = Flask(__name__)

# Try to import OpenCV and face detection modules with error handling
CV2_AVAILABLE = False
FACE_DETECTION_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenCV not available: {e}")
    CV2_AVAILABLE = False

# Initialize face detector and analyzer (with error handling)
detector = None
analyzer = None
feature_analyzer = None
advanced_tracker = None
micro_tracker = None
quadrant_tracker = None
eye_tracker = None
head_pose_tracker = None
dual_camera_tracker = None

if CV2_AVAILABLE:
    try:
        from face_detection import FaceDetector
        from face_analyzer import FaceAnalyzer
        from facial_features import FacialFeatureAnalyzer
        from advanced_tracking import AdvancedFaceTracker
        from micro_tracking import MicroExpressionTracker
        from quadrant_tracking import QuadrantTracker, EyeTracker, HeadPoseTracker
        from dual_camera import DualCameraTracker
        
        detector = FaceDetector()
        analyzer = FaceAnalyzer()
        feature_analyzer = FacialFeatureAnalyzer()
        advanced_tracker = AdvancedFaceTracker()
        micro_tracker = MicroExpressionTracker()
        quadrant_tracker = QuadrantTracker()
        eye_tracker = EyeTracker()
        head_pose_tracker = HeadPoseTracker()
        dual_camera_tracker = DualCameraTracker()
        FACE_DETECTION_AVAILABLE = True
    except Exception as e:
        print(f"Warning: Face detection modules not available: {e}")
        FACE_DETECTION_AVAILABLE = False

# Store previous quadrants for movement tracking
previous_quadrants = {}

# Store analysis for each client session
client_analyses = {}  # {session_id: analysis}
client_sessions = {}  # {session_id: session_data}

# Analysis lock for thread safety
analysis_lock = threading.Lock()

# Store current frame analysis for API access
current_analysis = {}

# CORS support for client-side camera
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": [
    "https://fullstacks.click",
    "https://www.fullstacks.click",
    "https://fullstacks-facial-recognition.vercel.app",
    "http://localhost:8080",
    "http://localhost:3000"
]}})

def base64_to_image(base64_string):
    """Convert base64 string to OpenCV image"""
    if not CV2_AVAILABLE:
        return None
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

def image_to_base64(image):
    """Convert OpenCV image to base64 string"""
    if not CV2_AVAILABLE:
        return None
    try:
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return image_base64
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def draw_corner_brackets(frame, x, y, w, h, color, thickness=2, length=20):
    """Draw corner brackets around detected face"""
    # Top-left
    cv2.line(frame, (x, y), (x + length, y), color, thickness)
    cv2.line(frame, (x, y), (x, y + length), color, thickness)
    # Top-right
    cv2.line(frame, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(frame, (x + w, y), (x + w, y + length), color, thickness)
    # Bottom-left
    cv2.line(frame, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(frame, (x, y + h), (x, y + h - length), color, thickness)
    # Bottom-right
    cv2.line(frame, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - length), color, thickness)

def draw_enhanced_detections(frame, analysis):
    """Draw detection boxes and tracking info on frame"""
    if not CV2_AVAILABLE:
        return frame
    if 'faces' not in analysis or not analysis['faces']:
        return frame
    
    for face_id, face_data in analysis['faces'].items():
        x, y, w, h = face_data.get('bbox', [0, 0, 0, 0])
        if w == 0 or h == 0:
            continue
        
        # Color based on face ID for tracking
        color = (0, 255, 0)  # Green for detected faces
        
        # Get features for this face
        features = face_data.get('features', {})
        
        # Enhanced tracking: quadrants, individual eyes, full head pose
        landmarks = features.get('landmarks', {})
        frame_time = time.time()
        
        # Track face quadrants
        quadrants = quadrant_tracker.divide_face_quadrants((x, y, w, h), landmarks)
        prev_quadrants = previous_quadrants.get(face_id)
        quadrant_movement = quadrant_tracker.analyze_quadrant_movement(quadrants, prev_quadrants) if quadrants else {}
        if quadrants:
            previous_quadrants[face_id] = quadrants
        
        # Track individual eyes
        individual_eyes = eye_tracker.track_individual_eyes(landmarks, (x, y, w, h), face_id, frame_time)
        
        # Calculate full 3D head pose
        full_head_pose = head_pose_tracker.calculate_full_head_pose(landmarks, (x, y, w, h))
        
        # Add to features
        if 'advanced' not in features:
            features['advanced'] = {}
        
        features['advanced']['quadrants'] = {
            'quadrants': quadrants,
            'movement': quadrant_movement
        } if quadrants else {}
        features['advanced']['individual_eyes'] = individual_eyes
        features['advanced']['full_head_pose'] = full_head_pose
        
        # Draw corner brackets instead of full rectangle
        draw_corner_brackets(frame, x, y, w, h, color, thickness=3, length=25)
        
        # Draw small ID label in top-left corner (minimal)
        cv2.putText(frame, f"ID:{face_id}", (x + 5, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Store features in face_data for API access
        face_data['features'] = features
    
    return frame

def serialize_value(value):
    """Recursively serialize numpy types and deques to JSON-compatible types"""
    if isinstance(value, (np.integer, np.int64)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64)):
        return float(value)
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, deque):
        return list(value)
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    return value

@app.route('/')
def index():
    """Serve the main page"""
    if not FACE_DETECTION_AVAILABLE:
        return render_template('index.html', error_message="Face detection is not available in this environment. Please use Railway or a local deployment.")
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Explicitly serve static files for Vercel compatibility"""
    try:
        return app.send_static_file(path)
    except Exception as e:
        print(f"Error serving static file {path}: {e}")
        return "File not found", 404

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """Process a frame sent from the client browser"""
    if not FACE_DETECTION_AVAILABLE:
        return jsonify({
            'status': 'error', 
            'message': 'Face detection is not available in Vercel serverless environment. Please deploy to Railway or use local deployment.'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'frame' not in data:
            return jsonify({'status': 'error', 'message': 'No frame data provided'}), 400
        
        session_id = data.get('session_id', 'default')
        frame_base64 = data['frame']
        
        # Convert base64 to OpenCV image
        frame = base64_to_image(frame_base64)
        if frame is None:
            return jsonify({'status': 'error', 'message': 'Invalid image data'}), 400
        
        # Analyze faces (detection + tracking + metrics)
        analysis = analyzer.analyze_faces(frame)
        
        # Draw enhanced detections with tracking info
        processed_frame = draw_enhanced_detections(frame.copy(), analysis)
        
        # Store analysis for API access
        with analysis_lock:
            global current_analysis
            current_analysis = analysis
            
            # Store for client session
            client_analyses[session_id] = analysis
            
            # Update dual camera tracker (if multiple sessions)
            if 'faces' in analysis:
                faces_data = {}
                for face_id, face_data in analysis['faces'].items():
                    if 'features' in face_data:
                        faces_data[face_id] = face_data
                dual_camera_tracker.update_camera_data(session_id, faces_data)
        
        # Convert processed frame back to base64
        processed_frame_base64 = image_to_base64(processed_frame)
        
        return jsonify({
            'status': 'success',
            'processed_frame': processed_frame_base64,
            'analysis': serialize_value(analysis)
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/facial_features')
def get_facial_features():
    """API endpoint to get detailed facial features"""
    try:
        session_id = request.args.get('session_id', 'default')
        
        with analysis_lock:
            analysis = client_analyses.get(session_id, current_analysis)
        
        if not analysis or 'faces' not in analysis:
            return jsonify({
                'status': 'success',
                'faces': []
            })
        
        faces_data = []
        for face_id, face_data in analysis['faces'].items():
            features = face_data.get('features', {})
            advanced = features.get('advanced', {})
            
            # Get blink info
            blink_info = advanced.get('blink', {})
            if not blink_info:
                blink_info = features.get('blink', {})
            
            faces_data.append({
                'id': face_id,
                'bbox': face_data.get('bbox', [0, 0, 0, 0]),
                'confidence': float(features.get('confidence', 0)),
                'landmarks': serialize_value(features.get('landmarks', {})),
                'expression': features.get('expression', 'neutral'),
                'emotion': features.get('emotion', 'neutral'),
                'age': int(features.get('age', 0)),
                'gender': features.get('gender', 'unknown'),
                'eye_status': features.get('eye_status', {}),
                'mouth_status': features.get('mouth_status', {}),
                'head_pose': serialize_value(features.get('head_pose', {})),
                'gaze': serialize_value(advanced.get('gaze', {})),
                'quality': serialize_value(advanced.get('quality', {})),
                'symmetry': float(features.get('symmetry', 0)),
                'position': {
                    'center': [int(x) for x in face_data.get('center', [0, 0])],
                    'area': int(face_data.get('area', 0))
                },
                'age_gender': serialize_value(advanced.get('age_gender', {})),
                'blink': serialize_value(blink_info),
                'action_units': serialize_value(advanced.get('action_units', {})),
                'face_roll': serialize_value(advanced.get('face_roll', {})),
                'expression_stats': serialize_value(advanced.get('expression_stats', {})),
                'eye_movements': serialize_value(advanced.get('eye_movements', {})),
                'mouth_movements': serialize_value(advanced.get('mouth_movements', {})),
                'micro_expressions': serialize_value(advanced.get('micro_expressions', {})),
                'quadrants': serialize_value(advanced.get('quadrants', {})),
                'individual_eyes': serialize_value(advanced.get('individual_eyes', {})),
                'full_head_pose': serialize_value(advanced.get('full_head_pose', {}))
            })
        
        return jsonify({
            'status': 'success',
            'faces': faces_data,
            'count': analysis.get('count', 0),
            'unique_faces': analysis.get('unique_faces', 0),
            'max_faces': analysis.get('max_faces', 0),
            'total_detections': analysis.get('total_detections', 0),
            'session_duration': analysis.get('session_duration', 0),
            'avg_faces_per_sec': float(analysis.get('avg_faces_per_sec', 0))
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    """Reset session statistics"""
    try:
        session_id = request.get_json().get('session_id', 'default') if request.is_json else 'default'
        
        analyzer.reset_session()
        advanced_tracker.reset()
        micro_tracker.reset()
        quadrant_tracker.reset()
        eye_tracker.reset()
        
        with analysis_lock:
            if session_id in client_analyses:
                del client_analyses[session_id]
            current_analysis = {}
        
        return jsonify({'status': 'success', 'message': 'Statistics reset'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cross_reference')
def get_cross_reference():
    """API endpoint to get cross-reference validation results"""
    try:
        results = dual_camera_tracker.cross_reference_detections()
        summary = dual_camera_tracker.get_cross_reference_summary()
        
        return jsonify({
            'status': 'success',
            'results': serialize_value(results),
            'summary': serialize_value(summary)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import os
    # Get port from environment variable (for cloud deployment) or use default
    port = int(os.environ.get('PORT', 8080))
    # Get host from environment or use 0.0.0.0 for network access
    host = os.environ.get('HOST', '0.0.0.0')
    # Debug mode based on environment
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    print("Starting Face Detection Web Server...")
    print(f"Open your browser and navigate to: http://localhost:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

