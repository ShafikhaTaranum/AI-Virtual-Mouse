# 🖱️ AI Virtual Mouse: Touchless Computer Control

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange.svg)

An advanced, highly optimized computer vision application that completely replaces a physical mouse and keyboard. By utilizing a webcam and Google's MediaPipe framework, this script translates real-time hand gestures into precise Operating System commands.



## ✨ Key Features
Unlike standard virtual mouse tutorials, this project is built for **performance, ergonomics, and reliability**:
* **Zero-Overlap Gestures:** Custom-mapped, biologically distinct hand shapes ensure the AI never confuses a click with a scroll.
* **Multithreaded Architecture:** Heavy I/O tasks (like taking screenshots or changing monitor brightness) are offloaded to background threads, maintaining a buttery-smooth 30+ FPS webcam feed.
* **Ergonomic "Active Zone":** Uses NumPy linear interpolation to map a small bounding box in the center of the camera to the entire monitor, eliminating arm fatigue.
* **Bulletproof Math:** Uses Euclidean distance (`math.hypot`) instead of simple X/Y axis comparisons, ensuring gestures work flawlessly regardless of hand rotation or left/right hand usage.
* **State-Tracking (Drag & Drop):** Advanced pinch-detection logic that tracks ongoing states across multiple video frames to allow seamless clicking and dragging.

## 🛠️ Technology Stack
* **Python** (Core Logic)
* **OpenCV / `cv2`** (Video Capture & Image Processing)
* **MediaPipe** (Real-time 3D Hand Landmark Detection)
* **PyAutoGUI & Pynput** (Direct OS-Level Hardware Control)
* **NumPy** (Mathematical Interpolation)

## 🚀 Installation & Setup

**1. Clone the repository:**
```bash
git clone [https://github.com/ShafikhaTaranum/AI-Virtual-Mouse.git](https://github.com/ShafikhaTaranum/AI-Virtual-Mouse.git)
cd AI-Virtual-Mouse
