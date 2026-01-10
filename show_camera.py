#!/usr/bin/env python3
"""
Simple Pi Camera Display
Shows live camera feed in OpenCV window
"""

import cv2
from camera_wrapper import Camera
import time

print("="*60)
print("PI CAMERA LIVE DISPLAY")
print("="*60)
print()

# Initialize camera
print("Initializing Pi Camera...")
camera = Camera(use_pi_camera=True, preview=False)

if not camera.isOpened():
    print("[ERROR] Failed to open camera")
    exit(1)

print("✓ Camera initialized")
print()
print("Opening display window...")
print("Press 'q' to quit")
print()

# Create window
window_name = "Pi Camera - Press 'q' to quit"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 640, 480)

frame_count = 0
start_time = time.time()

try:
    while True:
        # Capture frame
        ret, frame = camera.read()
        
        if not ret or frame is None:
            print("[ERROR] Failed to capture frame")
            break
        
        frame_count += 1
        
        # Calculate FPS
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps = frame_count / elapsed
        else:
            fps = 0
        
        # Add info overlay
        cv2.putText(frame, f"FPS: {fps:.1f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", 
                   (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Display frame
        cv2.imshow(window_name, frame)
        
        # Check for quit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n[INFO] Quitting...")
            break

except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user")

finally:
    # Cleanup
    camera.release()
    cv2.destroyAllWindows()
    
    # Show statistics
    elapsed = time.time() - start_time
    if elapsed > 0:
        avg_fps = frame_count / elapsed
        print(f"\n✓ Displayed {frame_count} frames in {elapsed:.1f}s")
        print(f"✓ Average FPS: {avg_fps:.2f}")

print("\n✓ Camera closed")
