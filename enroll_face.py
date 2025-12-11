"""
Face Enrollment Script
Used to register new faces into the system
"""

import cv2
import argparse
import sys
import os
import time
from face_recognizer import FaceRecognizer
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
    print("[INFO] Please look at the camera and press SPACE to capture each sample")
    
    # Initialize camera
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
            time.sleep(2)  # Warm up
            use_pi_cam = True
        except Exception as e:
            print(f"[ERROR] Pi Camera failed: {e}")
            print("[INFO] Falling back to USB camera")
            camera = cv2.VideoCapture(0)
            use_pi_cam = False
    else:
        camera = cv2.VideoCapture(0)
        use_pi_cam = False
        print("[INFO] Using USB camera")
    
    # Initialize recognizer
    recognizer = FaceRecognizer()
    
    samples_captured = 0
    best_sample = None
    
    print("\n[INFO] Camera ready. Press SPACE to capture, ESC to cancel")
    
    while samples_captured < num_samples:
        # Capture frame
        if use_pi_cam:
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            ret, frame = camera.read()
            if not ret:
                print("[ERROR] Failed to capture frame")
                break
        
        # Display frame with instructions
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Samples: {samples_captured}/{num_samples}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press SPACE to capture", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Enroll Face', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("\n[INFO] Enrollment cancelled")
            break
        elif key == 32:  # SPACE
            print(f"[INFO] Capturing sample {samples_captured + 1}...")
            
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
                print("[ERROR] No face detected. Please try again.")
            
            time.sleep(0.5)  # Brief pause
    
    # Cleanup
    cv2.destroyAllWindows()
    if use_pi_cam:
        camera.stop()
    else:
        camera.release()
    
    # Add the best sample to database
    if best_sample is not None and samples_captured > 0:
        print(f"\n[INFO] Adding {name} to face database...")
        if recognizer.add_face(name, best_sample):
            print(f"[SUCCESS] {name} enrolled successfully!")
            print(f"[INFO] Total known faces: {len(recognizer.list_known_faces())}")
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
    parser.add_argument('--name', type=str, required=True, help='Name of the person')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples to capture (default: 5)')
    parser.add_argument('--list', action='store_true', help='List all enrolled faces')
    parser.add_argument('--remove', type=str, help='Remove a face from database')
    
    args = parser.parse_args()
    
    recognizer = FaceRecognizer()
    
    if args.list:
        print("\n[INFO] Enrolled faces:")
        faces = recognizer.list_known_faces()
        if faces:
            for i, name in enumerate(faces, 1):
                print(f"  {i}. {name}")
        else:
            print("  No faces enrolled yet")
        return
    
    if args.remove:
        if recognizer.remove_face(args.remove):
            print(f"[SUCCESS] {args.remove} removed from database")
        else:
            print(f"[ERROR] Failed to remove {args.remove}")
        return
    
    # Enroll new face
    capture_face_samples(args.name, args.samples)


if __name__ == "__main__":
    main()
