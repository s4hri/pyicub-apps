# iFaceDetector

The **`iFaceDetector`** is a real-time, YARP-compatible perception module that detects the **midpoint between a person’s eyes** using [MediaPipe Pose](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker). It publishes the coordinates of this midpoint via YARP Bottle ports in **2D pixel space**.

---

## Features

- **Real-time** image processing from YARP streams (e.g., `/grabber`, iCub).
- Calculates and publishes:
  - **2D pixel midpoint** between detected eyes.

---

## Input/Output Ports

| Port                    | Type            | Description                                 |
|-------------------------|-----------------|---------------------------------------------|
| `/iFaceDetector/image:i` | `yarp.ImageRgb` | Input image stream (e.g., from `/grabber`). |
| `/iFaceDetector/eyes:o`  | `yarp.Bottle`   | Output midpoint coordinates `(u, v)` in pixel space. |

---

## Dependencies

- **Python 3**
- **OpenCV** (`opencv-python`)
- **NumPy** (`numpy`)
- **MediaPipe** (`mediapipe`)

---

## Usage

To run with the default period (0.1 s):

```bash
cd FaceDetector/
python3 app.py
```

Or to specify a custom period:

```bash
cd FaceDetector/
python3 app.py --period 0.1
```

Connect your camera/image source to the module:

```bash
yarp connect /grabber /iFaceDetector/image:i
```

Read the midpoint output from the module:

```bash
yarp read /anyname --from /iFaceDetector/eyes:o
```

---

## Output Example

**2D Pixel Output (`/iFaceDetector/eyes:o`)**:

```
yarp read ... /iFaceDetector/eyes:o
...
327 198
```

---

## Notes

- Outputs are provided only when both eyes are confidently detected (visibility > 0.5).
- The module uses `model_complexity=1` in MediaPipe Pose for balanced performance and accuracy.


## Authors

- Joel W. George Currie (joel.currie@iit.it)
- Davide De Tommaso (davide.detommaso@iit.it)
