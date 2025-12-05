import cv2
import platform

class CameraCapabilities:
    """Manage camera capabilities and optimize settings per camera type"""
    
    def __init__(self):
        self.camera_profiles = {
            # Generic laptop/built-in cameras (most common)
            'Laptop Built-in Camera': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection', 'Good for wide angle'],
                'use_case': 'Primary camera for most users'
            },
            'Built-in Camera': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection'],
                'use_case': 'Primary camera'
            },
            'Default Camera': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection'],
                'use_case': 'Primary camera'
            },
            # MacBook specific (fallback to generic if not found)
            'MacBook Air Built-in Camera': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection', 'Good for wide angle'],
                'use_case': 'Primary or wide-angle view'
            },
            'MacBook Air Built-in Camera (720p)': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection'],
                'use_case': 'Primary camera'
            },
            'MacBook Air Built-in Camera (1080p)': {
                'optimal_resolution': (1920, 1080),
                'fps': 30,
                'quality': 'Good',
                'features': ['HD resolution'],
                'use_case': 'Primary camera'
            },
            # iPhone cameras (enhanced, but optional)
            'iPhone 16 Pro Max': {
                'optimal_resolution': (1920, 1080),
                'fps': 60,
                'quality': 'Excellent',
                'features': ['High resolution', 'Better low light', 'Portrait mode capable'],
                'use_case': 'High-quality detection and analysis'
            },
            'iPhone 13 Pro Max': {
                'optimal_resolution': (1920, 1080),
                'fps': 60,
                'quality': 'Excellent',
                'features': ['High resolution', 'Good low light'],
                'use_case': 'High-quality detection and analysis'
            },
            'iPhone Camera': {
                'optimal_resolution': (1920, 1080),
                'fps': 60,
                'quality': 'Excellent',
                'features': ['High resolution'],
                'use_case': 'High-quality detection'
            },
            'iPhone Camera (1080p) - Check Model': {
                'optimal_resolution': (1920, 1080),
                'fps': 60,
                'quality': 'Excellent',
                'features': ['High resolution'],
                'use_case': 'High-quality detection'
            },
            # External cameras (generic)
            'External Camera (possibly iPhone)': {
                'optimal_resolution': (1920, 1080),
                'fps': 30,
                'quality': 'Good',
                'features': ['External camera'],
                'use_case': 'Secondary or primary camera'
            },
            'External Camera 0': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['External camera'],
                'use_case': 'Secondary camera'
            },
            'Camera 0 - Check Resolution': {
                'optimal_resolution': (1280, 720),
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection'],
                'use_case': 'Primary camera'
            }
        }
    
    def get_optimal_settings(self, camera_name):
        """Get optimal camera settings based on camera type"""
        # Try exact match first
        profile = self.camera_profiles.get(camera_name, {})
        
        # If no exact match, try to find a generic match
        if not profile:
            # Check for built-in/laptop patterns
            if any(keyword in camera_name.lower() for keyword in ['built-in', 'laptop', 'default', 'facetime', 'isight']):
                profile = self.camera_profiles.get('Laptop Built-in Camera', {})
            # Check for iPhone patterns
            elif 'iphone' in camera_name.lower():
                profile = self.camera_profiles.get('iPhone Camera', {})
            # Check for external patterns
            elif 'external' in camera_name.lower():
                profile = self.camera_profiles.get('External Camera (possibly iPhone)', {})
            # Default fallback
            else:
                profile = self.camera_profiles.get('Default Camera', {})
        
        # Fallback to safe defaults if still no profile
        if not profile:
            profile = {
                'optimal_resolution': (1280, 720),  # Safe default for most cameras
                'fps': 30,
                'quality': 'Good',
                'features': ['Standard detection'],
                'use_case': 'General detection'
            }
        
        return {
            'width': profile.get('optimal_resolution', (1280, 720))[0],
            'height': profile.get('optimal_resolution', (1280, 720))[1],
            'fps': profile.get('fps', 30),
            'quality': profile.get('quality', 'Good'),
            'features': profile.get('features', ['Standard detection']),
            'use_case': profile.get('use_case', 'General detection')
        }
    
    def configure_camera(self, camera, camera_name):
        """Configure camera with optimal settings"""
        settings = self.get_optimal_settings(camera_name)
        
        if camera and camera.isOpened():
            # Set resolution
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings['width'])
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings['height'])
            
            # Try to set FPS (may not work on all cameras)
            camera.set(cv2.CAP_PROP_FPS, settings['fps'])
            
            # Enable auto-focus if available (iPhone cameras)
            if 'iPhone' in camera_name:
                camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            # Set exposure (iPhone cameras handle this well)
            if 'iPhone' in camera_name:
                camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto exposure
            
            return settings
        
        return None
    
    def recommend_camera_pairing(self, available_cameras):
        """Recommend best camera pairing for dual camera mode"""
        recommendations = []
        
        # Need at least 2 cameras for dual mode
        if len(available_cameras) < 2:
            return recommendations
        
        # Categorize cameras
        builtin_cams = []
        iphone_cams = []
        external_cams = []
        
        for cam in available_cameras:
            name = cam.get('name', '').lower()
            quality_score = cam.get('quality_score', 0)
            
            if 'iphone' in name:
                iphone_cams.append(cam)
            elif any(keyword in name for keyword in ['built-in', 'laptop', 'macbook', 'facetime', 'isight']):
                builtin_cams.append(cam)
            else:
                external_cams.append(cam)
        
        # Sort by quality score
        builtin_cams.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        iphone_cams.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        external_cams.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Recommendation 1: iPhone + Built-in (best quality + validation)
        if iphone_cams and builtin_cams:
            recommendations.append({
                'primary': iphone_cams[0]['index'],
                'secondary': builtin_cams[0]['index'],
                'reason': 'Use iPhone for high-quality detection, built-in camera for wide-angle validation'
            })
        
        # Recommendation 2: Dual iPhone (maximum quality)
        if len(iphone_cams) >= 2:
            recommendations.append({
                'primary': iphone_cams[0]['index'],
                'secondary': iphone_cams[1]['index'],
                'reason': 'Dual iPhone setup for maximum quality and cross-validation'
            })
        
        # Recommendation 3: Best quality + second best (generic)
        if len(available_cameras) >= 2:
            sorted_cams = sorted(available_cameras, key=lambda x: x.get('quality_score', 0), reverse=True)
            if sorted_cams[0]['quality_score'] > sorted_cams[1]['quality_score']:
                recommendations.append({
                    'primary': sorted_cams[0]['index'],
                    'secondary': sorted_cams[1]['index'],
                    'reason': 'Use highest quality camera as primary, second best for validation'
                })
        
        # Recommendation 4: Built-in + External (common setup)
        if builtin_cams and external_cams:
            recommendations.append({
                'primary': builtin_cams[0]['index'],
                'secondary': external_cams[0]['index'],
                'reason': 'Use built-in camera as primary, external camera for different angle'
            })
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def get_camera_quality_score(self, camera_name, resolution):
        """Calculate quality score for camera selection"""
        # Try exact match first
        profile = self.camera_profiles.get(camera_name, {})
        
        # If no exact match, try generic match
        if not profile:
            if any(keyword in camera_name.lower() for keyword in ['built-in', 'laptop', 'default', 'facetime', 'isight']):
                profile = self.camera_profiles.get('Laptop Built-in Camera', {})
            elif 'iphone' in camera_name.lower():
                profile = self.camera_profiles.get('iPhone Camera', {})
            elif 'external' in camera_name.lower():
                profile = self.camera_profiles.get('External Camera (possibly iPhone)', {})
            else:
                profile = self.camera_profiles.get('Default Camera', {})
        
        base_score = 50  # Default for unknown cameras
        
        # Quality bonus from profile
        quality_bonus = {
            'Excellent': 30,
            'Good': 15,
            'Fair': 5
        }
        profile_quality = profile.get('quality', 'Good') if profile else 'Good'
        base_score += quality_bonus.get(profile_quality, 15)
        
        # Resolution bonus (works for any camera)
        width, height = resolution
        if width >= 1920 and height >= 1080:
            base_score += 20
        elif width >= 1280 and height >= 720:
            base_score += 10
        elif width >= 640 and height >= 480:
            base_score += 5
        
        # iPhone bonus (better sensors, but not required)
        if 'iPhone' in camera_name:
            base_score += 15
            if 'Pro Max' in camera_name:
                base_score += 10  # Latest model bonus
        
        # Built-in cameras get a small bonus for reliability
        if any(keyword in camera_name.lower() for keyword in ['built-in', 'laptop', 'facetime', 'isight']):
            base_score += 5
        
        return min(100, base_score)


