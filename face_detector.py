"""
Face Detection Module
Handles real-time face detection using OpenCV
"""

import cv2
import numpy as np
import sys
import os
import time
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
    
    from camera_wrapper import Camera
    
    detector = FaceDetector()
    
    # Use camera wrapper with preview
    camera = Camera(config.CAMERA_WIDTH, config.CAMERA_HEIGHT, 
                   config.USE_PI_CAMERA, preview=True)
    
    if not camera.isOpened():
        print("[ERROR] No camera available!")
        print("[INFO] Camera test skipped")
        sys.exit(0)
    
    print("[INFO] Showing live preview for 5 seconds...")
    print("[INFO] Press 'q' to quit early")
    
    cv2.namedWindow("Face Detection Test", cv2.WINDOW_NORMAL)
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 5:
        # Capture frame
        ret, frame = camera.read()
        
        if not ret or frame is None:
            print("[ERROR] Failed to capture frame")
            break
        
        frame_count += 1
        
        # Detect faces
        faces = detector.detect_faces(frame)
        
        # Draw detection boxes
        display_frame = detector.draw_faces(frame, faces) if len(faces) > 0 else frame.copy()
        
        # Add info
        cv2.putText(display_frame, f"Detected: {len(faces)} face(s)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press 'q' to quit", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("Face Detection Test", display_frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    print(f"[INFO] Processed {frame_count} frames")
    print(f"[INFO] Detected {len(faces)} face(s) in last frame")
    
    # Save final frame
    output_path = os.path.join(config.IMAGES_DIR, 'test_detection.jpg')
    if len(faces) > 0:
        output = detector.draw_faces(frame, faces)
        cv2.imwrite(output_path, output)
        print(f"[INFO] Test image with detections saved to {output_path}")
    else:
        cv2.imwrite(output_path, frame)
        print(f"[INFO] No faces detected. Frame saved to {output_path}")
    
    # Cleanup
    cv2.destroyAllWindows()
    camera.release()
    
    print("[INFO] Test complete")
