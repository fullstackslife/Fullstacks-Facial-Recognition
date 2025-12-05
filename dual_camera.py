import cv2
import numpy as np
import threading
import time
from collections import defaultdict

class DualCameraTracker:
    def __init__(self):
        self.camera_data = {}  # Store data from each camera
        self.cross_reference_results = {}  # Cross-referenced validation results
        self.camera_locks = {}  # Locks for each camera
        
    def register_camera(self, camera_id):
        """Register a camera for dual tracking"""
        if camera_id not in self.camera_data:
            self.camera_data[camera_id] = {
                'faces': {},
                'last_update': 0,
                'frame_count': 0
            }
            self.camera_locks[camera_id] = threading.Lock()
    
    def update_camera_data(self, camera_id, faces_data):
        """Update face data from a camera"""
        if camera_id not in self.camera_data:
            self.register_camera(camera_id)
        
        with self.camera_locks[camera_id]:
            self.camera_data[camera_id]['faces'] = faces_data
            self.camera_data[camera_id]['last_update'] = time.time()
            self.camera_data[camera_id]['frame_count'] += 1
    
    def cross_reference_detections(self):
        """Cross-reference detections between cameras to validate and improve accuracy"""
        if len(self.camera_data) < 2:
            return {}
        
        results = {}
        
        # Get all camera IDs
        camera_ids = list(self.camera_data.keys())
        
        # Compare each pair of cameras
        for i, cam1_id in enumerate(camera_ids):
            for cam2_id in camera_ids[i+1:]:
                comparison_key = f"{cam1_id}_vs_{cam2_id}"
                
                with self.camera_locks[cam1_id]:
                    cam1_faces = self.camera_data[cam1_id]['faces'].copy()
                
                with self.camera_locks[cam2_id]:
                    cam2_faces = self.camera_data[cam2_id]['faces'].copy()
                
                # Cross-reference face counts
                face_count_match = len(cam1_faces) == len(cam2_faces)
                
                # Cross-reference expressions
                expression_matches = self.compare_expressions(cam1_faces, cam2_faces)
                
                # Cross-reference blink counts
                blink_matches = self.compare_blinks(cam1_faces, cam2_faces)
                
                # Cross-reference head poses
                pose_matches = self.compare_head_poses(cam1_faces, cam2_faces)
                
                # Calculate overall confidence
                total_checks = len(expression_matches) + len(blink_matches) + len(pose_matches)
                matches = sum(expression_matches.values()) + sum(blink_matches.values()) + sum(pose_matches.values())
                confidence = matches / total_checks if total_checks > 0 else 0.5
                
                results[comparison_key] = {
                    'face_count_match': face_count_match,
                    'expression_matches': expression_matches,
                    'blink_matches': blink_matches,
                    'pose_matches': pose_matches,
                    'overall_confidence': confidence,
                    'validation_status': 'Validated' if confidence > 0.7 else 'Needs Review'
                }
        
        self.cross_reference_results = results
        return results
    
    def compare_expressions(self, faces1, faces2):
        """Compare expressions between cameras"""
        matches = {}
        
        # Match faces by position or use first available
        if len(faces1) > 0 and len(faces2) > 0:
            # For simplicity, compare first face from each camera
            # In production, you'd match faces by position/similarity
            face1 = list(faces1.values())[0] if faces1 else None
            face2 = list(faces2.values())[0] if faces2 else None
            
            if face1 and face2 and 'features' in face1 and 'features' in face2:
                expr1 = face1['features'].get('expression', {}).get('expression', 'Unknown')
                expr2 = face2['features'].get('expression', {}).get('expression', 'Unknown')
                matches['expression'] = expr1 == expr2
        
        return matches
    
    def compare_blinks(self, faces1, faces2):
        """Compare blink counts between cameras"""
        matches = {}
        
        if len(faces1) > 0 and len(faces2) > 0:
            face1 = list(faces1.values())[0] if faces1 else None
            face2 = list(faces2.values())[0] if faces2 else None
            
            if face1 and face2 and 'features' in face1 and 'features' in face2:
                # Get synchronized blink count (the accurate one)
                blink1 = 0
                blink2 = 0
                
                advanced1 = face1['features'].get('advanced', {})
                advanced2 = face2['features'].get('advanced', {})
                
                individual_eyes1 = advanced1.get('individual_eyes', {})
                individual_eyes2 = advanced2.get('individual_eyes', {})
                
                if individual_eyes1:
                    blink1 = individual_eyes1.get('synchronized_blink_count', 0)
                if individual_eyes2:
                    blink2 = individual_eyes2.get('synchronized_blink_count', 0)
                
                # Allow small difference (1-2 blinks) due to timing
                blink_diff = abs(blink1 - blink2)
                matches['blinks'] = blink_diff <= 2
        
        return matches
    
    def compare_head_poses(self, faces1, faces2):
        """Compare head poses between cameras"""
        matches = {}
        
        if len(faces1) > 0 and len(faces2) > 0:
            face1 = list(faces1.values())[0] if faces1 else None
            face2 = list(faces2.values())[0] if faces2 else None
            
            if face1 and face2 and 'features' in face1 and 'features' in face2:
                advanced1 = face1['features'].get('advanced', {})
                advanced2 = face2['features'].get('advanced', {})
                
                pose1 = advanced1.get('full_head_pose', {})
                pose2 = advanced2.get('full_head_pose', {})
                
                if pose1 and pose2:
                    # Compare yaw, pitch, roll (allow 5 degree tolerance)
                    yaw_match = abs(pose1.get('yaw', 0) - pose2.get('yaw', 0)) <= 5
                    pitch_match = abs(pose1.get('pitch', 0) - pose2.get('pitch', 0)) <= 5
                    roll_match = abs(pose1.get('roll', 0) - pose2.get('roll', 0)) <= 5
                    
                    matches['yaw'] = yaw_match
                    matches['pitch'] = pitch_match
                    matches['roll'] = roll_match
        
        return matches
    
    def get_validated_data(self, camera_id):
        """Get validated/cross-referenced data for a camera"""
        if camera_id not in self.camera_data:
            return None
        
        base_data = self.camera_data[camera_id]['faces'].copy()
        
        # Add validation flags
        for face_id, face_data in base_data.items():
            if 'features' in face_data:
                face_data['features']['validated'] = {
                    'cross_referenced': len(self.cross_reference_results) > 0,
                    'confidence': self.cross_reference_results.get('overall_confidence', 0.5) if self.cross_reference_results else 0.5
                }
        
        return base_data
    
    def get_cross_reference_summary(self):
        """Get summary of cross-referencing results"""
        if not self.cross_reference_results:
            return None
        
        summary = {
            'total_comparisons': len(self.cross_reference_results),
            'validated_detections': 0,
            'needs_review': 0,
            'average_confidence': 0
        }
        
        total_confidence = 0
        for comp_key, result in self.cross_reference_results.items():
            if result['validation_status'] == 'Validated':
                summary['validated_detections'] += 1
            else:
                summary['needs_review'] += 1
            total_confidence += result['overall_confidence']
        
        if len(self.cross_reference_results) > 0:
            summary['average_confidence'] = total_confidence / len(self.cross_reference_results)
        
        return summary


