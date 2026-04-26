import cv2
import numpy as np

# Empty function required for OpenCV trackbars
def nothing(x):
    pass

print("--- HSV CALIBRATION TOOL INITIATING ---")

# Connect to your phone camera
url = 'http://192.168.0.136:4747/video' # Double check this is still correct!
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("CRITICAL ERROR: Cannot connect to phone.")
    exit()

# Create the control window
cv2.namedWindow('Controls')
cv2.resizeWindow('Controls', 400, 300)

# Create sliders (Trackbars) for Min and Max HSV
# We start V_Min at 200 because we know we are looking for a bright light
cv2.createTrackbar('H_Min', 'Controls', 0, 179, nothing)
cv2.createTrackbar('S_Min', 'Controls', 0, 255, nothing)
cv2.createTrackbar('V_Min', 'Controls', 200, 255, nothing)

cv2.createTrackbar('H_Max', 'Controls', 179, 179, nothing)
cv2.createTrackbar('S_Max', 'Controls', 255, 255, nothing)
cv2.createTrackbar('V_Max', 'Controls', 255, 255, nothing)

print("Running! Adjust the sliders until ONLY the flame is white in the Mask window.")
print("Press 'q' to quit and print your final values.")

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.resize(frame, (640, 480))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Read the current position of all 6 sliders
    h_min = cv2.getTrackbarPos('H_Min', 'Controls')
    s_min = cv2.getTrackbarPos('S_Min', 'Controls')
    v_min = cv2.getTrackbarPos('V_Min', 'Controls')
    
    h_max = cv2.getTrackbarPos('H_Max', 'Controls')
    s_max = cv2.getTrackbarPos('S_Max', 'Controls')
    v_max = cv2.getTrackbarPos('V_Max', 'Controls')
    
    print(f"LIVE VALUES -> Min: [{h_min}, {s_min}, {v_min}] | Max: [{h_max}, {s_max}, {v_max}]", end='\r')

    # Apply the slider values to our array
    lower_bound = np.array([h_min, s_min, v_min])
    upper_bound = np.array([h_max, s_max, v_max])

    # Create the black-and-white mask
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    # Overlay the mask on the real image so you can see exactly what is being tracked
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Show the windows
    cv2.imshow('1. Original Camera', frame)
    cv2.imshow('2. The Mask (Robot Vision)', mask)
    cv2.imshow('3. Final Result', result)

    # Quit and print values
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n==================================")
        print("COPY THESE INTO YOUR MAIN SCRIPT:")
        print(f"lower_flame = np.array([{h_min}, {s_min}, {v_min}])")
        print(f"upper_flame = np.array([{h_max}, {s_max}, {v_max}])")
        print("==================================\n")
        break

cap.release()
cv2.destroyAllWindows()
