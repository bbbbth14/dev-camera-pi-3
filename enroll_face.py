"""
Face Enrollment Script
Used to register new faces into the system
"""

import cv2
import argparse
import sys
import os
import time
from datetime import datetime
from face_recognizer import FaceRecognizer
from camera_wrapper import Camera
from attendance_tracker import AttendanceTracker
import config


def capture_face_samples(name: str, num_samples: int = 5):
    """
    Capture multiple face samples for better recognition
    
    Args:
        name: Person's name
        num_samples: Number of samples to capture
    """
    print(f"\n[INFO] Enrolling new face: {name}")
    print(f"[INFO] Will capture {num_samples} samples")
    print("[INFO] Camera will capture automatically with 2 second intervals")
    print("[INFO] Position yourself in front of the camera")
    
    # Initialize camera with preview
    camera = Camera(config.CAMERA_WIDTH, config.CAMERA_HEIGHT, 
                   config.USE_PI_CAMERA, preview=True)
    
    if not camera.isOpened():
        print("[ERROR] Failed to open camera")
        return False
    
    # Initialize recognizer and face detector
    recognizer = FaceRecognizer()
    from face_detector import FaceDetector
    detector = FaceDetector()
    
    samples_captured = 0
    best_sample = None
    
    # Create preview window
    window_name = f"Enrolling: {name}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    print(f"[INFO] Starting capture in 3 seconds...")
    
    # Show countdown
    for i in range(3, 0, -1):
        ret, frame = camera.read()
        if ret and frame is not None:
            display = frame.copy()
            cv2.putText(display, f"Starting in {i}...", 
                       (display.shape[1]//2 - 100, display.shape[0]//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.imshow(window_name, display)
            cv2.waitKey(1000)
    
    while samples_captured < num_samples:
        # Capture frame
        ret, frame = camera.read()
        
        if not ret or frame is None:
            print("[ERROR] Failed to capture frame")
            break
        
        # Detect faces for preview
        faces = detector.detect_faces(frame)
        display_frame = frame.copy()
        
        # Draw face boxes
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Add info overlay
        cv2.putText(display_frame, f"Sample {samples_captured}/{num_samples}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Enrolling: {name}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show preview
        cv2.imshow(window_name, display_frame)
        cv2.waitKey(100)
        
        print(f"[INFO] Capturing sample {samples_captured + 1}/{num_samples}...")
        
        # Save sample image
        sample_dir = os.path.join(config.IMAGES_DIR, name)
        os.makedirs(sample_dir, exist_ok=True)
        sample_path = os.path.join(sample_dir, f"sample_{samples_captured + 1}.jpg")
        cv2.imwrite(sample_path, frame)
        
        # Try to encode the face
        encoding = recognizer.encode_face(frame)
        if encoding is not None:
            samples_captured += 1
            best_sample = frame
            print(f"[SUCCESS] Sample {samples_captured} captured successfully")
        else:
            print("[ERROR] No face detected. Please position yourself in front of camera.")
        
        if samples_captured < num_samples:
            time.sleep(2)  # Wait 2 seconds between captures
    
    # Cleanup
    cv2.destroyAllWindows()
    camera.release()
    
    # Add the best sample to database
    if best_sample is not None and samples_captured > 0:
        print(f"\n[INFO] Adding {name} to face database...")
        if recognizer.add_face(name, best_sample):
            # Generate and save User ID
            tracker = AttendanceTracker()
            user_id = tracker._get_or_create_user_id(name)
            
            print(f"[SUCCESS] {name} enrolled successfully!")
            print(f"[SUCCESS] User ID assigned: {user_id}")
            print(f"[INFO] Total known faces: {len(recognizer.list_known_faces())}")
            
            # Update User Directory in Excel
            tracker.update_user_directory()
            print(f"[INFO] User directory updated in Excel")
            
            return True
        else:
            print("[ERROR] Failed to add face to database")
            return False
    else:
        print("[ERROR] No valid samples captured")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enroll a new face into the system')
    parser.add_argument('--name', type=str, help='Name of the person')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples to capture (default: 5)')
    parser.add_argument('--list', action='store_true', help='List all enrolled faces')
    parser.add_argument('--remove', type=str, help='Remove a face from database')
    
    args = parser.parse_args()
    
    recognizer = FaceRecognizer()
    
    if args.list:
        print("\n[INFO] Enrolled faces:")
        faces = recognizer.list_known_faces()
        if faces:
            # Also show User IDs
            tracker = AttendanceTracker()
            print(f"\n{'#':<4} {'Name':<20} {'User ID':<15}")
            print("-" * 40)
            for i, name in enumerate(faces, 1):
                user_id = tracker._get_or_create_user_id(name)
                print(f"{i:<4} {name:<20} {user_id:<15}")
        else:
            print("  No faces enrolled yet")
        return
    
    if args.remove:
        if recognizer.remove_face(args.remove):
            print(f"[SUCCESS] {args.remove} removed from database")
        else:
            print(f"[ERROR] Failed to remove {args.remove}")
        return
    
    # Enroll new face requires name
    if not args.name:
        parser.error("--name is required for enrollment")
    
    # Enroll new face
    capture_face_samples(args.name, args.samples)


if __name__ == "__main__":
    main()
