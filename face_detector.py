"""
Face Detection Module
Handles real-time face detection using OpenCV
"""

import cv2
import numpy as np
from typing import List, Tuple
import config


class FaceDetector:
    """Face detector using OpenCV Haar Cascades"""
    
    def __init__(self):
        """Initialize the face detector"""
        # Load the pre-trained Haar Cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier")
        
        print("[INFO] Face detector initialized")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame
        
        Args:
            frame: Input image/frame
            
        Returns:
            List of face bounding boxes as (x, y, w, h) tuples
        """
        # Convert to grayscale for better detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=config.DETECTION_SCALE_FACTOR,
            minNeighbors=config.DETECTION_MIN_NEIGHBORS,
            minSize=config.DETECTION_MIN_SIZE
        )
        
        return faces
    
    def draw_faces(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]], 
                   labels: List[str] = None) -> np.ndarray:
        """
        Draw bounding boxes around detected faces
        
        Args:
            frame: Input image/frame
            faces: List of face bounding boxes
            labels: Optional labels for each face
            
        Returns:
            Frame with drawn bounding boxes
        """
        output = frame.copy()
        
        for i, (x, y, w, h) in enumerate(faces):
            # Draw rectangle
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label if provided
            if labels and i < len(labels):
                label = labels[i]
                # Draw background for text
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(output, (x, y - text_height - 10), 
                            (x + text_width, y), (0, 255, 0), -1)
                # Draw text
                cv2.putText(output, label, (x, y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return output
    
    def extract_face_roi(self, frame: np.ndarray, face: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract face region of interest from frame
        
        Args:
            frame: Input image/frame
            face: Face bounding box (x, y, w, h)
            
        Returns:
            Cropped face image
        """
        x, y, w, h = face
        return frame[y:y+h, x:x+w]


if __name__ == "__main__":
    """Test the face detector"""
    print("[INFO] Testing face detector...")
    
    detector = FaceDetector()
    
    # Try to open camera
    if config.USE_PI_CAMERA:
        try:
            from picamera2 import Picamera2
            camera = Picamera2()
            camera_config = camera.create_preview_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)}
            )
            camera.configure(camera_config)
            camera.start()
            print("[INFO] Using Pi Camera")
            
            import time
            time.sleep(2)  # Warm up camera
            
            # Capture and test
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"[ERROR] Pi Camera failed: {e}")
            print("[INFO] Falling back to USB camera")
            camera = cv2.VideoCapture(0)
            ret, frame = camera.read()
    else:
        camera = cv2.VideoCapture(0)
        ret, frame = camera.read()
        print("[INFO] Using USB camera")
    
    # Detect faces
    faces = detector.detect_faces(frame)
    print(f"[INFO] Detected {len(faces)} face(s)")
    
    # Draw and show result
    if len(faces) > 0:
        output = detector.draw_faces(frame, faces)
        cv2.imwrite('/home/bienth/cameraPI/data/test_detection.jpg', output)
        print("[INFO] Test image saved to data/test_detection.jpg")
    
    # Cleanup
    if config.USE_PI_CAMERA:
        try:
            camera.stop()
        except:
            pass
    else:
        camera.release()
    
    print("[INFO] Test complete")
