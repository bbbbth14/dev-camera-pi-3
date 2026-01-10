# Face Recognition Algorithm - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Algorithm Architecture](#algorithm-architecture)
3. [Face Detection](#face-detection)
4. [Face Recognition](#face-recognition)
5. [Training Process](#training-process)
6. [Recognition Flow](#recognition-flow)
7. [Technical Specifications](#technical-specifications)
8. [Performance Optimization](#performance-optimization)

---

## Overview

This face recognition system uses **OpenCV** with **LBPH (Local Binary Patterns Histograms)** for face recognition and **Haar Cascade Classifiers** for face detection. This combination is optimized for Raspberry Pi and provides a good balance between accuracy and performance.

### Why LBPH?
- **Lightweight**: Runs efficiently on Raspberry Pi
- **No External Dependencies**: Uses only OpenCV
- **Good Accuracy**: Reliable for controlled environments
- **Fast Training**: Can retrain quickly when adding new faces
- **Low Memory**: Minimal resource requirements

---

## Algorithm Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FACE RECOGNITION SYSTEM                   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐     ┌───────▼────────┐
        │ Face Detection │     │ Face Recognition│
        │  (Haar Cascade)│     │      (LBPH)     │
        └────────────────┘     └─────────────────┘
                │                       │
        ┌───────▼────────┐     ┌───────▼────────┐
        │   Preprocessing │     │  Face Encoding  │
        │  - Grayscale    │     │  - LBP Features │
        │  - Scale Factor │     │  - Histograms   │
        │  - Min Size     │     │  - Comparison   │
        └─────────────────┘     └─────────────────┘
```

---

## Face Detection

### 1. Haar Cascade Classifier

**What is it?**
- Machine learning-based object detection method
- Uses cascade function trained from positive and negative images
- Detects faces by looking for specific features (edges, lines, patterns)

**Process:**

```python
# 1. Load the pre-trained Haar Cascade classifier
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# 2. Convert image to grayscale (faster processing)
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 3. Detect faces
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # How much image size is reduced at each scale
    minNeighbors=5,       # How many neighbors each rectangle should have
    minSize=(30, 30)      # Minimum face size to detect
)
```

### 2. Detection Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **scaleFactor** | 1.1 | Image pyramid scale reduction (1.05 - 1.4) |
| **minNeighbors** | 5 | Minimum neighbors for detection (3-6 typical) |
| **minSize** | (30, 30) | Minimum face size in pixels |

**How it works:**

1. **Image Pyramid**: Creates multiple scales of the image
   ```
   Original (640x480) → 580x435 → 527x395 → ...
   ```

2. **Sliding Window**: Moves a detection window across each scale
   ```
   ┌─────────────────────┐
   │    ┌──┐            │
   │    └──┘→           │  Scan entire image
   │                    │
   └─────────────────────┘
   ```

3. **Feature Detection**: Looks for facial features at each position
   - Eyes region (dark)
   - Nose bridge (light)
   - Mouth region (dark)

4. **Neighbor Filtering**: Combines overlapping detections
   ```
   Multiple detections → Group nearby → Single face box
   ```

### 3. Face Detection Output

Returns list of bounding boxes:
```python
faces = [(x, y, w, h), ...]
# x, y: Top-left corner coordinates
# w, h: Width and height of face rectangle
```

**Example:**
```
┌─────────────────────────────┐
│                             │
│     ┌───────────────┐      │
│     │   x,y         │      │  Face detected at (150, 100)
│     │       👤      │      │  Size: 200x200 pixels
│     │               │      │
│     └───────────────┘      │
│                             │
└─────────────────────────────┘
```

---

## Face Recognition

### 1. LBPH Algorithm (Local Binary Patterns Histograms)

**What is LBPH?**

LBPH is a texture descriptor that creates a unique fingerprint for each face by analyzing local patterns.

**Process:**

#### Step 1: Divide Face into Cells
```
Original Face (200x200)
┌─────────────────────┐
│  ┌───┬───┬───┬───┐ │
│  │ 1 │ 2 │ 3 │ 4 │ │  Divide into grid
│  ├───┼───┼───┼───┤ │  (e.g., 8x8 cells)
│  │ 5 │ 6 │ 7 │ 8 │ │
│  ├───┼───┼───┼───┤ │
│  │ 9 │10 │11 │12 │ │
│  └───┴───┴───┴───┘ │
└─────────────────────┘
```

#### Step 2: Calculate LBP for Each Pixel

For each pixel, compare with 8 neighbors:
```
    Neighbors          Binary          LBP Value
    88  95  102        0  0  1
    90 [100] 108  →    0  ●  1    →   01011100₂ = 92
    75  80   95        0  0  1
```

**Algorithm:**
```python
center = pixel_value
for each neighbor:
    if neighbor >= center:
        binary_value = 1
    else:
        binary_value = 0
LBP = concatenate all binary values → decimal
```

#### Step 3: Create Histograms

For each cell, create histogram of LBP values:
```
Cell Histogram:
Value:  0   1   2  ...  92  ... 255
Count: [5] [3] [8] ... [12] ... [4]
       └────────────────────────────┘
           256 bins
```

#### Step 4: Concatenate All Histograms

```
Final Feature Vector:
[Cell1_Hist] + [Cell2_Hist] + ... + [Cell64_Hist]
= 256 × 64 = 16,384 dimensional vector
```

### 2. Recognition Process

**Training Phase:**
```python
# For each enrolled user
for user in enrolled_users:
    # 1. Load all face images
    images = load_user_images(user)
    
    # 2. Extract LBP features
    features = []
    for image in images:
        lbp_features = calculate_lbp(image)
        features.append(lbp_features)
    
    # 3. Train LBPH model
    model.train(features, labels)
```

**Recognition Phase:**
```python
# 1. Detect face in frame
face_roi = detect_face(frame)

# 2. Extract LBP features
test_features = calculate_lbp(face_roi)

# 3. Compare with trained model
label, confidence = model.predict(test_features)

# 4. Make decision
if confidence < 70:  # Lower is better for LBPH
    name = known_names[label]
else:
    name = "Unknown"
```

### 3. Confidence Score

**LBPH Confidence:**
- **Lower = Better Match** (opposite of typical)
- **Range:** 0 to ~150+
- **Thresholds:**
  - `< 50`: Excellent match
  - `50-70`: Good match ✓ (our threshold)
  - `70-90`: Fair match
  - `> 90`: Poor match (Unknown)

**Why confidence is inverse?**
LBPH confidence represents the distance between histograms:
```
Distance = √Σ(histogram1 - histogram2)²
```
Smaller distance = more similar = better match

---

## Training Process

### 1. Enrollment Workflow

```
User Enrollment
    │
    ├─> 1. Capture Multiple Samples (5 photos)
    │        │
    │        ├─> Photo 1 (face at center)
    │        ├─> Photo 2 (slight left)
    │        ├─> Photo 3 (slight right)
    │        ├─> Photo 4 (normal light)
    │        └─> Photo 5 (varied expression)
    │
    ├─> 2. Detect Face in Each Sample
    │        └─> Using Haar Cascade
    │
    ├─> 3. Extract Face ROI (Region of Interest)
    │        └─> Resize to 200x200 pixels
    │
    ├─> 4. Convert to Grayscale
    │        └─> Remove color information
    │
    ├─> 5. Save Samples to disk
    │        └─> data/images/{name}/sample_*.jpg
    │
    └─> 6. Train LBPH Model
         └─> Update recognizer
```

### 2. Training Algorithm

```python
def train():
    encodings = []
    labels = []
    names = []
    
    # For each user directory
    for user_name in user_directories:
        # Get user label (index)
        if user_name not in names:
            names.append(user_name)
        user_label = names.index(user_name)
        
        # Process each image
        for image_file in user_images:
            # Load image
            image = cv2.imread(image_file)
            
            # Detect face
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Extract first face
            (x, y, w, h) = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Add to training set
            encodings.append(face_roi)
            labels.append(user_label)
    
    # Train LBPH model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(encodings, np.array(labels))
    
    return recognizer, names
```

### 3. Storage Structure

```
data/
├── images/
│   ├── John/
│   │   ├── sample_1.jpg  ← 200x200 grayscale
│   │   ├── sample_2.jpg
│   │   ├── sample_3.jpg
│   │   ├── sample_4.jpg
│   │   └── sample_5.jpg
│   ├── Mary/
│   │   ├── sample_1.jpg
│   │   └── ...
│   └── ...
└── faces/
    └── encodings.pkl  ← Serialized model (optional)
```

---

## Recognition Flow

### Complete Recognition Pipeline

```
┌──────────────────────────────────────────────────────────┐
│ 1. CAPTURE FRAME                                         │
│    Camera → 640x480 BGR image                           │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 2. CONVERT TO GRAYSCALE                                  │
│    BGR → Grayscale (faster processing)                  │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 3. DETECT FACES                                          │
│    Haar Cascade → List of (x, y, w, h)                  │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 4. EXTRACT FACE ROI                                      │
│    Crop face region → Resize to 200x200                 │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 5. CALCULATE LBP FEATURES                                │
│    LBPH.predict() → label, confidence                    │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 6. COMPARE CONFIDENCE                                    │
│    if confidence < 70: MATCH                             │
│    else: UNKNOWN                                         │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 7. RETURN RESULT                                         │
│    name = "John" or "Unknown"                            │
└──────────────────────────────────────────────────────────┘
```

### Code Example

```python
def recognize_person(frame):
    # 1. Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    results = []
    
    # 3. Process each detected face
    for (x, y, w, h) in faces:
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, (200, 200))
        
        # 4. Predict identity
        label, confidence = recognizer.predict(face_roi)
        
        # 5. Check confidence threshold
        if confidence < 70:
            name = known_names[label]
            results.append((name, confidence, (x, y, w, h)))
        else:
            results.append(("Unknown", confidence, (x, y, w, h)))
    
    return results
```

---

## Technical Specifications

### System Requirements

| Component | Specification |
|-----------|--------------|
| **Processor** | Raspberry Pi 3/4 or equivalent |
| **RAM** | Minimum 1GB |
| **Camera** | Pi Camera or USB Webcam |
| **Resolution** | 640x480 minimum |
| **Frame Rate** | 15-30 FPS |

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Detection Speed** | ~30ms per frame |
| **Recognition Speed** | ~10ms per face |
| **Training Time** | ~2s for 10 users × 5 images |
| **Memory Usage** | ~50MB for 50 enrolled users |
| **Accuracy** | ~90-95% in controlled lighting |

### Parameter Tuning

#### Detection Parameters

```python
# Adjust for environment
DETECTION_SCALE_FACTOR = 1.1   # 1.05 = slower but more accurate
                               # 1.3  = faster but may miss faces

DETECTION_MIN_NEIGHBORS = 5    # 3 = detect more (false positives)
                               # 7 = detect less (miss some faces)

DETECTION_MIN_SIZE = (30, 30)  # Minimum face size
                               # Smaller = detect distant faces
                               # Larger = ignore small faces
```

#### Recognition Parameters

```python
# Confidence threshold
CONFIDENCE_THRESHOLD = 70      # Lower = stricter matching
                               # Higher = more lenient

# Face size
FACE_SIZE = (200, 200)         # Standard face size
                               # Larger = more detail but slower
                               # Smaller = faster but less accurate
```

---

## Performance Optimization

### 1. Frame Processing Optimization

**Process Every Nth Frame:**
```python
frame_count = 0
PROCESS_EVERY_N_FRAMES = 2  # Process every 2nd frame

while True:
    frame = camera.read()
    frame_count += 1
    
    if frame_count % PROCESS_EVERY_N_FRAMES == 0:
        # Perform face detection/recognition
        results = recognize_faces(frame)
    
    # Always display (use cached results)
    display_results(frame, results)
```

**Benefits:**
- 2× faster processing
- Minimal accuracy loss
- Smoother video display

### 2. Image Preprocessing

**Grayscale Conversion:**
```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```
- Reduces data by 66% (3 channels → 1)
- Faster cascade detection
- Less memory usage

**Face Resizing:**
```python
face_roi = cv2.resize(face_roi, (200, 200))
```
- Standardizes input size
- Consistent feature extraction
- Faster LBP computation

### 3. Multi-Sample Training

**Why 5 samples per person?**
- **1 sample:** Poor accuracy, no variation
- **3 samples:** Basic coverage
- **5 samples:** Good balance ✓
- **10+ samples:** Better but slower training

**Sample Capture Strategy:**
```python
samples = [
    "Center face",           # Base reference
    "Slight left turn",      # Angle variation
    "Slight right turn",     # Angle variation  
    "Different expression",  # Expression variation
    "Varied lighting"        # Lighting variation
]
```

### 4. Memory Management

**Lazy Loading:**
```python
# Don't keep all images in memory
def train():
    for image_file in image_files:
        image = cv2.imread(image_file)  # Load
        encoding = process(image)        # Process
        del image                        # Free memory
```

**Model Persistence:**
```python
# Save trained model to avoid retraining
recognizer.write('model.yml')

# Load when needed
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('model.yml')
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **No face detected** | Poor lighting | Improve lighting, adjust minNeighbors |
| **Wrong person recognized** | Similar features | Retrain with more samples |
| **High confidence scores** | Poor image quality | Improve camera quality, lighting |
| **Slow performance** | Processing every frame | Use PROCESS_EVERY_N_FRAMES |
| **Memory errors** | Too many users | Implement model persistence |

### Accuracy Improvements

1. **Lighting:** Consistent, even lighting is crucial
2. **Angle:** Face directly toward camera
3. **Distance:** 1-2 meters optimal
4. **Samples:** More samples = better accuracy
5. **Quality:** Higher resolution = better features

---

## References

### OpenCV Documentation
- Haar Cascade: https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html
- LBPH: https://docs.opencv.org/4.x/df/d25/tutorial_face_landmark_detector_in_opencvhtml

### Research Papers
- Viola-Jones Face Detection (2001)
- LBPH Face Recognition (Ahonen et al., 2006)

### Implementation Files
- `face_detector.py` - Haar Cascade implementation
- `face_recognizer.py` - LBPH recognition implementation
- `config.py` - Parameter configuration

---

**Last Updated:** January 10, 2026
**Version:** 1.0
