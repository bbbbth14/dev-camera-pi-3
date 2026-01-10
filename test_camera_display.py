#!/usr/bin/env python3
"""
Test Pi Camera Display
Simple script to verify camera can capture and display frames
"""

import cv2
import time
from camera_wrapper import Camera

print("="*60)
print("PI CAMERA DISPLAY TEST")
print("="*60)
print()

# Try to initialize camera
print("Initializing Pi Camera...")
camera = Camera(use_pi_camera=True, preview=False)

if not camera.isOpened():
    print("[ERROR] Failed to open camera")
    print("\nTrying alternative method...")
    import subprocess
    result = subprocess.run(['rpicam-still', '--help'], capture_output=True)
    if result.returncode == 0:
        print("✓ rpicam-still is available")
    else:
        print("✗ rpicam-still not found")
    exit(1)

print("✓ Camera initialized")
print()
print("Capturing frames...")
print("Press Ctrl+C to stop")
print()

frame_count = 0
start_time = time.time()

try:
    # Test 1: Capture 10 frames without display
    print("Test 1: Capturing frames (no display)...")
    for i in range(10):
        ret, frame = camera.read()
        if ret and frame is not None:
            frame_count += 1
            print(f"  Frame {i+1}: {frame.shape} - OK")
        else:
            print(f"  Frame {i+1}: FAILED")
        time.sleep(0.5)
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    print(f"\n✓ Captured {frame_count} frames in {elapsed:.2f}s ({fps:.2f} fps)")
    
    # Test 2: Try to display with OpenCV (may fail in headless mode)
    print("\nTest 2: Attempting to display with OpenCV window...")
    try:
        window_name = "Pi Camera Test"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        can_display = True
        print("✓ OpenCV window created")
    except Exception as e:
        can_display = False
        print(f"✗ Cannot create OpenCV window: {e}")
        print("  This is normal if running headless (no X display)")
    
    if can_display:
        print("\nDisplaying camera feed...")
        print("Press 'q' to quit")
        
        for i in range(50):  # Show 50 frames
            ret, frame = camera.read()
            if ret and frame is not None:
                # Add some text overlay
                cv2.putText(frame, f"Frame: {i+1}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'q' to quit", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                cv2.imshow(window_name, frame)
                
                key = cv2.waitKey(100) & 0xFF
                if key == ord('q'):
                    break
        
        cv2.destroyAllWindows()
    else:
        print("\nTest 3: Saving frames to files instead...")
        for i in range(3):
            ret, frame = camera.read()
            if ret and frame is not None:
                filename = f"test_frame_{i+1}.jpg"
                cv2.imwrite(filename, frame)
                print(f"  Saved: {filename}")
            time.sleep(1)
        print("\n✓ Check the saved images to verify camera works")

except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    camera.release()
    print("\n✓ Camera released")

print()
print("="*60)
print("TEST COMPLETE")
print("="*60)
print()
print("Summary:")
print(f"  - Frames captured: {frame_count}")
print(f"  - Camera: {'Working' if frame_count > 0 else 'Not working'}")
print()
