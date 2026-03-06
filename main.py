import cv2
import mediapipe as mp
import pyautogui
import random
import time
import math
import threading
import numpy as np
import screen_brightness_control as sbc
from pynput.mouse import Button, Controller

# ==========================================
# 1. SETTINGS & VARIABLES
# ==========================================
gesture_delay = 0.8
last_action_time = 0

# Active Zone & Camera Variables
cam_width, cam_height = 640, 480
frame_reduction = 100  # The padding around the edge of the camera

# Smoothing variables
smoothing_factor = 5
prev_x, prev_y = 0, 0 

# Dragging state variable
is_dragging = False

mouse = Controller()
screen_width, screen_height = pyautogui.size()

# Disable PyAutoGUI's built-in delay to prevent loop bottlenecks
pyautogui.PAUSE = 0 

# ==========================================
# 2. MEDIAPIPE SETUP
# ==========================================
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)
draw = mp.solutions.drawing_utils


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def fingers_up(landmarks):
    fingers = []
    
    # THUMB: Bulletproof math using distance from tip to pinky knuckle
    dist_tip = math.hypot(landmarks[4][0] - landmarks[17][0], landmarks[4][1] - landmarks[17][1])
    dist_base = math.hypot(landmarks[2][0] - landmarks[17][0], landmarks[2][1] - landmarks[17][1])
    
    if dist_tip > dist_base:
        fingers.append(1) # Thumb extended
    else:
        fingers.append(0) # Thumb tucked

    # INDEX, MIDDLE, RING, PINKY
    fingers.append(1 if landmarks[8][1] < landmarks[6][1] else 0)
    fingers.append(1 if landmarks[12][1] < landmarks[10][1] else 0)
    fingers.append(1 if landmarks[16][1] < landmarks[14][1] else 0)
    fingers.append(1 if landmarks[20][1] < landmarks[18][1] else 0)

    return fingers

def move_mouse(landmarks):
    global prev_x, prev_y
    
    # 1. Convert normalized MediaPipe coordinates into actual camera pixels
    x_cam = landmarks[8][0] * cam_width
    y_cam = landmarks[8][1] * cam_height
    
    # 2. Map the small camera box to the massive monitor screen
    target_x = np.interp(x_cam, (frame_reduction, cam_width - frame_reduction), (0, screen_width))
    target_y = np.interp(y_cam, (frame_reduction, cam_height - frame_reduction), (0, screen_height))
    
    # 3. Apply smoothing formula
    curr_x = prev_x + (target_x - prev_x) / smoothing_factor
    curr_y = prev_y + (target_y - prev_y) / smoothing_factor
    
    # 4. Move mouse using pynput
    mouse.position = (curr_x, curr_y)
    
    # 5. Update previous coordinates
    prev_x, prev_y = curr_x, curr_y

def take_screenshot_in_background():
    img = pyautogui.screenshot()
    img.save(f"screenshot_{random.randint(1,1000)}.png")
    
def change_brightness_in_background(level):
    try:
        sbc.set_brightness(level)
    except Exception as e:
        pass

# ==========================================
# 4. GESTURE DETECTION
# ==========================================
def detect_gesture(frame, landmark_list):
    global last_action_time, is_dragging

    if len(landmark_list) < 21:
        return

    current_time = time.time()
    thumb, index, middle, ring, pinky = fingers_up(landmark_list)

    # Calculate distance between Thumb tip (4) and Index tip (8) for pinching
    pinch_dist = math.hypot(landmark_list[8][0] - landmark_list[4][0], 
                            landmark_list[8][1] - landmark_list[4][1])

    # -------- 1. DRAG AND DROP --------
    # Gesture: Pinch (Thumb tip and Index tip touching)
    # Middle, Ring, and Pinky must be strictly DOWN.
    if middle == 0 and ring == 0 and pinky == 0:
        if pinch_dist < 0.05:  
            if not is_dragging:
                mouse.press(Button.left)
                is_dragging = True
            
            move_mouse(landmark_list) 
            cv2.putText(frame, "Dragging...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return  
            
        elif is_dragging and pinch_dist >= 0.05:
            mouse.release(Button.left)
            is_dragging = False

    # -------- 2. MOVE MOUSE --------
    # Gesture: Pointing (Index Finger UP only)
    # Array: [0, 1, 0, 0, 0]
    if thumb == 0 and index == 1 and middle == 0 and ring == 0 and pinky == 0:
        move_mouse(landmark_list)
        cv2.putText(frame, "Moving Mouse", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # -------- 3. LEFT CLICK --------
    # Gesture: L-Shape (Thumb + Index UP)
    # Array: [1, 1, 0, 0, 0]
    elif thumb == 1 and index == 1 and middle == 0 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.click()
        cv2.putText(frame, "Left Click", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        last_action_time = current_time

    # -------- 4. RIGHT CLICK --------
    # Gesture: Pinky promise (Pinky UP only)
    # Array: [0, 0, 0, 0, 1]
    elif thumb == 0 and index == 0 and middle == 0 and ring == 0 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.rightClick()
        cv2.putText(frame, "Right Click", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        last_action_time = current_time

    # -------- 5. DOUBLE CLICK --------
    # Gesture: Shaka / Call Me (Thumb + Pinky UP)
    # Array: [1, 0, 0, 0, 1]
    elif thumb == 1 and index == 0 and middle == 0 and ring == 0 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.doubleClick()
        cv2.putText(frame, "Double Click", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        last_action_time = current_time

    # -------- 6. VOLUME UP --------
    # Gesture: Peace Sign (Index + Middle UP)
    # Array: [0, 1, 1, 0, 0]
    elif thumb == 0 and index == 1 and middle == 1 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.press("volumeup")
        cv2.putText(frame, "Volume Up", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        last_action_time = current_time

    # -------- 7. VOLUME DOWN --------
    # Gesture: 3 Fingers (Thumb + Index + Middle UP)
    # Array: [1, 1, 1, 0, 0]
    elif thumb == 1 and index == 1 and middle == 1 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.press("volumedown")
        cv2.putText(frame, "Volume Down", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        last_action_time = current_time

    # -------- 8. BRIGHTNESS HIGH (MULTITHREADED) --------
    # # Gesture: Open Palm (All 5 Fingers UP)
    # Array: [1, 1, 1, 1, 1]

    elif thumb == 1 and index == 1 and middle == 1 and ring == 1 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        
        threading.Thread(target=change_brightness_in_background, args=(100,)).start()
        cv2.putText(frame, "Brightness 100%", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        last_action_time = current_time

    # -------- 9. BRIGHTNESS LOW (MULTITHREADED) --------
    # Gesture: 4 Fingers UP (Thumb tucked in)
    # Array: [0, 1, 1, 1, 1]
    
    elif thumb == 0 and index == 1 and middle == 1 and ring == 1 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        
        threading.Thread(target=change_brightness_in_background, args=(20,)).start()
        cv2.putText(frame, "Brightness 20%", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
        last_action_time = current_time
    
    # -------- 10. SCREENSHOT (MULTITHREADED) --------
    # Gesture: Closed Fist (All fingers DOWN)
    # Array: [0, 0, 0, 0, 0]
    elif thumb == 0 and index == 0 and middle == 0 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        threading.Thread(target=take_screenshot_in_background).start()
        cv2.putText(frame, "Screenshot Saved", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        last_action_time = current_time

    # -------- 11. SHOW DESKTOP (BOSS KEY) --------
    # Gesture: OK Sign (Middle + Ring + Pinky UP, Thumb & Index tucked)
    # Array: [0, 0, 1, 1, 1]
    elif thumb == 0 and index == 0 and middle == 1 and ring == 1 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.hotkey('win', 'd') 
        cv2.putText(frame, "Show Desktop", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        last_action_time = current_time + 1.0 

    # -------- 12. CONTINUOUS SCROLL DOWN --------
    # Gesture: Spiderman (Thumb + Index + Pinky UP)
    # Array: [1, 1, 0, 0, 1]
    elif thumb == 1 and index == 1 and middle == 0 and ring == 0 and pinky == 1:
        pyautogui.scroll(-60) 
        cv2.putText(frame, "Scrolling...", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

    # -------- 13. SWITCH WINDOWS (ALT + ESC) --------
    # Gesture: 3 Fingers (Index + Middle + Ring UP)
    # Array: [0, 1, 1, 1, 0]
    elif thumb == 0 and index == 1 and middle == 1 and ring == 1 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.hotkey('alt', 'esc')
        cv2.putText(frame, "Switch Window", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 100), 2)
        last_action_time = current_time + 1.5 

    # -------- 14. NEXT SLIDE (PPT) --------
    # Gesture: Hitchhiker (Thumb UP only)
    # Array: [1, 0, 0, 0, 0]
    elif thumb == 1 and index == 0 and middle == 0 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.press('right')
        cv2.putText(frame, "Next Slide", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        last_action_time = current_time + 0.5 

    # -------- 15. PREVIOUS SLIDE (PPT) --------
    # Gesture: Rock On (Index + Pinky UP)
    # Array: [0, 1, 0, 0, 1]
    elif thumb == 0 and index == 1 and middle == 0 and ring == 0 and pinky == 1 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.press('left')
        cv2.putText(frame, "Previous Slide", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        last_action_time = current_time + 0.5

    # -------- 16. ZOOM IN --------
    # Gesture: Snap shape 1 (Thumb + Middle Finger UP)
    # Array: [1, 0, 1, 0, 0]
    elif thumb == 1 and index == 0 and middle == 1 and ring == 0 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(50) 
        pyautogui.keyUp('ctrl')
        cv2.putText(frame, "Zoom In", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 150, 0), 2)
        last_action_time = current_time + 0.1

    # -------- 17. ZOOM OUT --------
    # Gesture: Snap shape 2 (Thumb + Ring Finger UP)
    # Array: [1, 0, 0, 1, 0]
    elif thumb == 1 and index == 0 and middle == 0 and ring == 1 and pinky == 0 \
            and current_time - last_action_time > gesture_delay:
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-50) 
        pyautogui.keyUp('ctrl')
        cv2.putText(frame, "Zoom Out", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 150, 0), 2)
        last_action_time = current_time + 0.1

# ==========================================
# 5. MAIN LOOP
# ==========================================
def main():
    cap = cv2.VideoCapture(0)
    
    # Force the camera to our specific resolution to keep the Active Zone math accurate
    cap.set(3, cam_width)
    cap.set(4, cam_height)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        
        # --- DRAW THE ACTIVE ZONE RECTANGLE ---
        cv2.rectangle(frame, (frame_reduction, frame_reduction), 
                      (cam_width - frame_reduction, cam_height - frame_reduction),
                      (255, 0, 255), 2)

        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frameRGB)

        landmark_list = []

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)

            for lm in hand_landmarks.landmark:
                landmark_list.append((lm.x, lm.y))

        detect_gesture(frame, landmark_list)

        cv2.imshow("Virtual Mouse", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()