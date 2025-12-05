import cv2
import platform
import subprocess
import re

def get_camera_name_macos(index):
    """Try to get camera name on macOS using system_profiler or IORegistry"""
    try:
        # Method 1: Try system_profiler
        result = subprocess.run(
            ['system_profiler', 'SPCameraDataType'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # Parse camera names from system_profiler output
            lines = result.stdout.split('\n')
            cameras = []
            
            for i, line in enumerate(lines):
                # Look for camera model names
                if 'Model ID:' in line or 'Name:' in line:
                    match = re.search(r':\s*(.+)', line)
                    if match:
                        name = match.group(1).strip()
                        if name and name not in cameras:
                            cameras.append(name)
            
            # Try to match by index
            if index < len(cameras):
                return cameras[index]
        
        # Method 2: Try IORegistry to get device names
        try:
            result = subprocess.run(
                ['ioreg', '-p', 'IOUSB', '-w0', '-r'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # This is more complex, but we can try
                pass
        except:
            pass
            
    except Exception as e:
        pass
    
    return None

def identify_camera_type(index, resolution, backend):
    """Identify camera type based on properties"""
    width, height = resolution
    
    # On macOS with AVFoundation backend
    if platform.system() == 'Darwin' and backend == 'AVFOUNDATION':
        # Try to get actual name first
        name = get_camera_name_macos(index)
        if name:
            # Clean up the name - prioritize generic patterns first
            name_lower = name.lower()
            
            # Generic built-in/laptop cameras (most common - works for any laptop)
            if any(keyword in name_lower for keyword in ['facetime', 'built-in', 'isight', 'integrated', 'webcam']):
                # Check if it's MacBook-specific (optional enhancement)
                if 'macbook' in name_lower:
                    return 'MacBook Air Built-in Camera'
                # Generic laptop camera (works for Windows, Linux, etc.)
                return 'Laptop Built-in Camera'
            # iPhone cameras (optional enhancement)
            elif 'iphone' in name_lower or 'continuity' in name_lower:
                # Try to identify specific iPhone model (optional)
                if '16' in name and ('pro max' in name_lower or 'promax' in name_lower):
                    return 'iPhone 16 Pro Max'
                elif '13' in name and ('pro max' in name_lower or 'promax' in name_lower):
                    return 'iPhone 13 Pro Max'
                elif '16' in name:
                    return 'iPhone 16 Pro Max'
                elif '13' in name:
                    return 'iPhone 13 Pro Max'
                return 'iPhone Camera'
            # Virtual cameras
            elif 'obs' in name_lower or 'virtual' in name_lower:
                return 'OBS Virtual Camera'
            # Return as-is for other cameras (USB webcams, etc.)
            return name
        
        # Heuristics based on index and resolution patterns
        # On macOS, when iPhone Continuity Camera is active:
        # - Index 0 is often the iPhone (high resolution, 1920x1080)
        # - Index 1 is usually the built-in FaceTime camera
        # - Lower resolutions might indicate built-in camera
        
        # Enhanced heuristics - works for any laptop setup
        # Most laptops have built-in camera at index 0 or 1
        # External cameras (iPhone, USB webcams) often have higher resolution
        
        if index == 1:
            # Index 1 is commonly the built-in camera on macOS/Windows
            if height == 720:
                return 'Laptop Built-in Camera (720p)'
            elif height == 1080:
                return 'Laptop Built-in Camera (1080p)'
            return 'Laptop Built-in Camera'
        elif index == 0:
            # Index 0 could be built-in or external
            if width >= 1920 and height >= 1080:
                # High res - likely external (iPhone, USB webcam)
                return 'External Camera (High Res)'
            elif height == 720 or (width == 1280 and height == 720):
                # Standard laptop resolution
                return 'Laptop Built-in Camera'
            return 'Camera 0'
        elif index == 2:
            # Additional external camera
            if width >= 1920 and height >= 1080:
                return 'External Camera (High Res)'
            return f'External Camera {index}'
        else:
            return f'External Camera {index}'
    
    # Generic fallback
    if index == 0:
        return 'Default Camera'
    else:
        return f'Camera {index}'

def list_available_cameras():
    """List all available camera devices with better identification"""
    available_cameras = []
    
    # Try cameras 0-10
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Try to get camera properties
            backend = cap.getBackendName()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Try to identify camera type
            camera_name = identify_camera_type(i, (width, height), backend)
            
            available_cameras.append({
                'index': i,
                'backend': backend,
                'resolution': (width, height),
                'name': camera_name,
                'display_name': f"{camera_name} ({width}x{height})"
            })
            cap.release()
    
    return available_cameras

def find_laptop_camera():
    """
    Find the laptop's built-in camera.
    On macOS, when an iPhone is connected via Continuity Camera:
    - Index 0 is often the iPhone camera
    - Index 1 is usually the built-in laptop camera
    """
    cameras = list_available_cameras()
    
    if not cameras:
        return 0  # Default fallback
    
    if len(cameras) == 1:
        return cameras[0]['index']
    
    # On macOS, prioritize index 1 for built-in camera when iPhone is connected
    if platform.system() == 'Darwin':
        # Check if index 1 exists (common for built-in camera)
        for cam in cameras:
            if cam['index'] == 1:
                print("Detected macOS: Using index 1 (likely built-in camera)")
                return 1
        
        # If index 1 doesn't exist, try to identify by resolution patterns
        # Built-in cameras often have specific resolutions
        # iPhone Continuity Camera might have different characteristics
        for cam in cameras:
            idx = cam['index']
            res = cam['resolution']
            # Built-in FaceTime cameras are often 1280x720 or 1920x1080
            # But we can't reliably distinguish, so prefer index 1 if available
            if idx == 1:
                return idx
    
    # Fallback: return index 1 if it exists, otherwise index 0
    for cam in cameras:
        if cam['index'] == 1:
            return 1
    
    return cameras[0]['index']

def get_camera_index():
    """Get the appropriate camera index, with fallback logic"""
    try:
        camera_idx = find_laptop_camera()
        print(f"Selected camera index: {camera_idx}")
        return camera_idx
    except Exception as e:
        print(f"Error detecting camera: {e}")
        print("Falling back to camera index 0")
        return 0

