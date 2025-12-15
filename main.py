"""
Main Application - Face Recognition System
Supports both attendance (check-in/check-out) and access control modes
"""

import cv2
import argparse
import time
import sys
from datetime import datetime
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from attendance_tracker import AttendanceTracker
from camera_wrapper import Camera
import config

# GPIO control (optional)
if config.USE_GPIO:
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.RELAY_PIN, GPIO.OUT)
        GPIO.output(config.RELAY_PIN, GPIO.LOW)
        print("[INFO] GPIO initialized for access control")
    except Exception as e:
        print(f"[WARNING] GPIO initialization failed: {e}")
        config.USE_GPIO = False


class FaceRecognitionSystem:
    """Main face recognition system"""
    
    def __init__(self, mode='attendance'):
        """
        Initialize the system
        
        Args:
            mode: 'attendance' for check-in/check-out, 'access' for access control
        """
        self.mode = mode
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizer()
        self.tracker = AttendanceTracker()
        self.frame_count = 0
        self.last_recognition = {}
        
        print(f"[INFO] System initialized in {mode.upper()} mode")
    
    def unlock_door(self):
        """Unlock door/box via GPIO relay"""
        if config.USE_GPIO:
            try:
                print("[INFO] Unlocking...")
                GPIO.output(config.RELAY_PIN, GPIO.HIGH)
                time.sleep(config.UNLOCK_DURATION)
                GPIO.output(config.RELAY_PIN, GPIO.LOW)
                print("[INFO] Locked")
            except Exception as e:
                print(f"[ERROR] Failed to control relay: {e}")
        else:
            print(f"[SIMULATED] Door unlocked for {config.UNLOCK_DURATION} seconds")
    
    def process_recognition(self, name: str, confidence: float):
        """
        Process a recognized face based on mode
        
        Args:
            name: Recognized person's name
            confidence: Recognition confidence
        """
        current_time = time.time()
        
        # Avoid duplicate processing within 2 seconds
        if name in self.last_recognition:
            if current_time - self.last_recognition[name] < 2.0:
                return
        
        self.last_recognition[name] = current_time
        
        if self.mode == 'attendance':
            # Check-in/Check-out mode
            if self.tracker.can_checkin(name):
                self.tracker.record_event(name, 'CHECK_IN', confidence)
                print(f"\n✓ CHECK-IN: {name} (Confidence: {confidence:.2f})")
            else:
                remaining = self.tracker.get_cooldown_remaining(name)
                minutes = remaining // 60
                seconds = remaining % 60
                print(f"\n⏳ {name} already checked in. Cooldown: {minutes}m {seconds}s")
        
        elif self.mode == 'access':
            # Access control mode
            if name != "Unknown":
                self.tracker.record_event(name, 'ACCESS_GRANTED', confidence)
                print(f"\n✓ ACCESS GRANTED: {name} (Confidence: {confidence:.2f})")
                self.unlock_door()
            else:
                self.tracker.record_event("Unknown", 'ACCESS_DENIED', confidence)
                print(f"\n✗ ACCESS DENIED: Unknown person")
    
    def run(self):
        """Run the main recognition loop"""
        print(f"\n[INFO] Starting {self.mode.upper()} system...")
        print("[INFO] Press 'q' to quit, 's' to show summary")
        print("[INFO] Live camera preview with face detection enabled")
        
        # Initialize camera using wrapper with preview enabled
        camera = Camera(config.CAMERA_WIDTH, config.CAMERA_HEIGHT, 
                       config.USE_PI_CAMERA, preview=True)
        
        if not camera.isOpened():
            print("[ERROR] Failed to open camera")
            return
        
        # Create window
        window_name = f"Face Recognition - {self.mode.upper()} Mode"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        try:
            while True:
                # Capture frame
                ret, frame = camera.read()
                
                if not ret or frame is None:
                    print("[ERROR] Failed to capture frame")
                    break
                
                self.frame_count += 1
                display_frame = frame.copy()
                
                # Process every Nth frame for performance
                if self.frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                    # Detect faces
                    faces = self.detector.detect_faces(frame)
                    
                    if len(faces) > 0:
                        # Recognize faces
                        results = self.recognizer.recognize_faces(frame)
                        
                        # Draw and process results
                        labels = []
                        for name, confidence in results:
                            label = f"{name} ({confidence:.2f})"
                            labels.append(label)
                            
                            # Process recognized faces
                            self.process_recognition(name, confidence)
                        
                        # Draw bounding boxes
                        display_frame = self.detector.draw_faces(display_frame, faces, labels)
                
                # Add system info overlay
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cv2.putText(display_frame, f"Mode: {self.mode.upper()}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, timestamp, 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press 'q' to quit | 's' for summary", 
                           (10, display_frame.shape[0] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Show frame with detections
                cv2.imshow(window_name, display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n[INFO] Shutting down...")
                    break
                elif key == ord('s'):
                    self.show_summary()
        
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
        
        finally:
            # Cleanup
            cv2.destroyAllWindows()
            camera.release()
            
            if config.USE_GPIO:
                GPIO.cleanup()
            
            print("[INFO] System stopped")
    
    def show_summary(self):
        """Display today's attendance summary"""
        summary = self.tracker.get_attendance_summary()
        
        print("\n" + "="*50)
        print("TODAY'S SUMMARY")
        print("="*50)
        print(f"Check-ins:        {summary['total_checkins']}")
        print(f"Check-outs:       {summary['total_checkouts']}")
        print(f"Access Granted:   {summary['total_access_granted']}")
        print(f"Access Denied:    {summary['total_access_denied']}")
        print(f"Unique People:    {summary['unique_people']}")
        print("="*50)
        
        # Show recent records
        records = self.tracker.get_today_attendance()
        if records:
            print("\nRECENT EVENTS:")
            for record in records[-5:]:
                print(f"  {record['Time']} - {record['Name']}: {record['Event']}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Face Recognition System for Attendance and Access Control'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['attendance', 'access'],
        default='attendance',
        help='System mode: attendance (check-in/out) or access (door control)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show today\'s summary and exit'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export attendance report to file'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    system = FaceRecognitionSystem(mode=args.mode)
    
    if args.summary:
        system.show_summary()
        return
    
    if args.export:
        system.tracker.export_report(args.export)
        print(f"[INFO] Report exported to {args.export}")
        return
    
    # Run the system
    system.run()


if __name__ == "__main__":
    main()
