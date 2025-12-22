# Display and Preview Guide

## Live Camera Preview Features

The system now includes **live camera preview** with face detection visualization:

### What You'll See:

#### 1. Face Detection Test (Option 6)
- **Live preview** for 5 seconds
- **Green rectangles** around detected faces
- Real-time face count display
- Press 'q' to quit early

#### 2. Face Enrollment (Option 1)
- **Live preview window** showing camera feed
- **Green boxes** around detected faces
- **Countdown timer** before capture starts
- Sample progress indicator (e.g., "Sample 2/5")
- Name being enrolled displayed on screen

#### 3. Attendance System (Option 2)
- **Full-screen live preview**
- **Face detection boxes** with labels
- **Name and confidence score** displayed above each face
- System info overlay:
  - Current mode (ATTENDANCE)
  - Timestamp
  - Controls reminder
- Real-time recognition feedback

#### 4. Access Control (Option 3)
- Similar to attendance mode
- Shows ACCESS GRANTED/DENIED status
- Live face tracking

### Display Elements:

```
┌─────────────────────────────────────┐
│ Mode: ATTENDANCE                    │ ← System mode
│ 2025-12-15 14:30:45                │ ← Timestamp
│                                     │
│     ┌──────────────────┐           │
│     │  John (0.85)     │           │ ← Name + confidence
│     │  ┌──────────┐    │           │
│     │  │          │    │           │ ← Face box
│     │  │   Face   │    │           │
│     │  │          │    │           │
│     │  └──────────┘    │           │
│     └──────────────────┘           │
│                                     │
│ Press 'q' to quit | 's' for summary│ ← Controls
└─────────────────────────────────────┘
```

### Color Coding:

- **Green boxes**: Detected faces
- **Green text**: System info and known faces
- **White text**: Instructions and labels
- **Red boxes**: (future) Unknown or denied access

### Controls:

- **'q'** - Quit the application
- **'s'** - Show attendance summary (in attendance mode)
- **ESC** - Cancel enrollment

## Running with Display

### On Raspberry Pi Desktop:
```bash
./start.sh
# Choose option 1, 2, 3, or 6 to see live preview
```

### Via SSH with X11 Forwarding:
```bash
# On your local machine, SSH with X11:
ssh -X pi@raspberry-pi-ip

cd /home/bienth/Documents/ras-cam-face/dev-camera-pi-3
./start.sh
```

### Via VNC:
1. Connect to Raspberry Pi via VNC
2. Open terminal
3. Run `./start.sh`
4. Windows will appear on the VNC desktop

## Window Names:

- **Face Detection Test** - Camera test (Option 6)
- **Enrolling: [Name]** - Enrollment window (Option 1)
- **Face Recognition - ATTENDANCE Mode** - Attendance system (Option 2)
- **Face Recognition - ACCESS Mode** - Access control (Option 3)

## Performance Tips:

1. **Frame Processing**: System processes every 2nd frame for better performance
2. **Window Size**: Windows are resizable (WINDOW_NORMAL flag)
3. **Camera Resolution**: Default 640x480, can be changed in config.py

## Troubleshooting:

### No Display Window?
- Check if you're running on desktop environment (not just SSH)
- Try: `echo $DISPLAY` - should show `:0` or similar
- For SSH: Use `ssh -X` for X11 forwarding

### Slow Performance?
- Increase `PROCESS_EVERY_N_FRAMES` in config.py
- Reduce camera resolution in config.py

### Window Too Small/Large?
- Windows are resizable - drag corners to resize
- Or modify `CAMERA_WIDTH` and `CAMERA_HEIGHT` in config.py
