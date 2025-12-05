import cv2
import sys

class FaceDetector:
    def __init__(self):
        # Load the pre-trained face cascade classifier
        # OpenCV includes this by default
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def detect_faces(self, frame):
        """Detect faces in a frame and return coordinates"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces
    
    def draw_detections(self, frame, faces):
        """Draw rectangles around detected faces"""
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add face count label
            cv2.putText(frame, f'Face', (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return frame

def main():
    # Initialize face detector
    detector = FaceDetector()
    
    # Detect and use laptop camera (not iPhone)
    from camera_utils import get_camera_index
    camera_index = get_camera_index()
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        sys.exit(1)
    
    # Set camera resolution (optional, for better performance)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Face Detection Started!")
    print("Press 'q' to quit")
    
    face_count = 0
    
    while True:
        # Read frame from camera
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Flip frame horizontally for mirror effect (optional)
        frame = cv2.flip(frame, 1)
        
        # Detect faces
        faces = detector.detect_faces(frame)
        face_count = len(faces)
        
        # Draw detections
        frame = detector.draw_detections(frame, faces)
        
        # Display face count
        cv2.putText(frame, f'Faces Detected: {face_count}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display instructions
        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show the frame
        cv2.imshow('Face Detection', frame)
        
        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("Face detection stopped.")

if __name__ == "__main__":
    main()

