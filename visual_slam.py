import cv2
import serial
import time
import numpy as np

# --- ROS 2 Imports ---
import rclpy
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

print("--- FULL AUTONOMOUS VISUAL SLAM INITIATING ---")

# ==========================================
# 1. INITIALIZE ROS 2 PUBLISHER
# ==========================================
rclpy.init()
ros_node = rclpy.create_node('visual_slam_node')
path_publisher = ros_node.create_publisher(Path, '/robot_path', 10)

robot_path = Path()
robot_path.header.frame_id = 'odom' 

global_x = 0.0
global_y = 0.0

# ==========================================
# 2. HARDWARE CONNECTIONS
# ==========================================
arduino_port = '/dev/ttyACM0' # UPDATE IF NEEDED
phone_camera_url = 'http://192.168.0.136:4747/video' # UPDATE TO YOUR PHONE IP

# Connect to Arduino
try:
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
    time.sleep(2)
except Exception as e:
    print(f"WARNING: Arduino failed to connect initially. Will keep trying. Error: {e}")
    arduino = None

# Connect to Camera
print("Connecting to phone camera over Wi-Fi...")
cap = cv2.VideoCapture(phone_camera_url)

if not cap.isOpened():
    print("CRITICAL ERROR: Cannot connect to phone.")
    exit()

# Optical Flow Setup (For RViz Odometry)
feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
lk_params = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

ret, old_frame = cap.read()
old_frame = cv2.resize(old_frame, (640, 480))
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

# Green Color Calibration (HSV)
lower_green = np.array([0, 0, 255])
upper_green = np.array([179, 41, 255])

print("--- SYSTEM GREEN. MOTORS ARMED. SEARCHING FOR TARGET ---")

# ==========================================
# 3. THE MAIN CONTROL LOOP
# ==========================================
try:
    while True:
        ret, frame = cap.read()
        if not ret: break
            
        frame = cv2.resize(frame, (640, 480))
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        screen_center_x = 640 // 2 

        # ---------------------------------------------------------
        # A. ODOMETRY: CALCULATE PATH & PUBLISH TO RVIZ
        # ---------------------------------------------------------
        if p0 is None or len(p0) < 10:
            p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
            
        if p0 is not None:
            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
            if p1 is not None:
                good_new = p1[st == 1]
                good_old = p0[st == 1]
                if len(good_new) > 0:
                    dx = np.mean(good_new[:, 0] - good_old[:, 0])
                    dy = np.mean(good_new[:, 1] - good_old[:, 1])

                    # Plot in RViz2 (Low scale factor to smooth out jitter)
                    scale_factor = 0.01 
                    global_x += dx * scale_factor
                    global_y -= dy * scale_factor 

                    current_pose = PoseStamped()
                    current_pose.header.frame_id = 'odom'
                    current_pose.header.stamp = ros_node.get_clock().now().to_msg()
                    current_pose.pose.position.x = float(global_x)
                    current_pose.pose.position.y = float(global_y)
                    current_pose.pose.position.z = 0.0 

                    robot_path.header.stamp = ros_node.get_clock().now().to_msg()
                    robot_path.poses.append(current_pose)
                    path_publisher.publish(robot_path)

                old_gray = frame_gray.copy()
                p0 = good_new.reshape(-1, 1, 2)
        
        # ---------------------------------------------------------
        # B. VISION & DECISION LOGIC
        # ---------------------------------------------------------
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_green, upper_green)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_found = False
        command = "x" # Default Stop

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000: # Found a valid green object
                target_found = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                object_center_x = x + (w // 2)
                cv2.circle(frame, (object_center_x, y + (h//2)), 5, (0, 0, 255), -1)

                # STEERING LOGIC (With wide 100px deadzone to prevent stuttering)
                if area > 80000: # Target is massive, we reached it!
                    command = "x"
                    cv2.putText(frame, "TARGET REACHED [STOPPING]", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                elif object_center_x < screen_center_x - 100:
                    command = "a"
                    cv2.putText(frame, "TRACKING: STEER LEFT", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                elif object_center_x > screen_center_x + 100:
                    command = "d"
                    cv2.putText(frame, "TRACKING: STEER RIGHT", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                else:
                    command = "w"
                    cv2.putText(frame, "TRACKING: DRIVE FORWARD", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                break 

        # If no target, spin to search
        if not target_found:
            command = "d" 
            cv2.putText(frame, "SEARCHING: SPINNING...", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # ---------------------------------------------------------
        # C. HARDWARE EXECUTION & CRASH RECOVERY
        # ---------------------------------------------------------
        if arduino is not None:
            try:
                arduino.write((command + '\n').encode())
            except serial.SerialException:
                print("WARNING: USB DROPPED! Attempting to reconnect...")
                cv2.putText(frame, "USB ERROR: RECONNECTING...", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                try:
                    arduino.close()
                    time.sleep(0.5) 
                    arduino = serial.Serial(arduino_port, 9600, timeout=1)
                except:
                    arduino = None # Failed to reconnect this frame, try again later

        # Process ROS 2
        rclpy.spin_once(ros_node, timeout_sec=0.01)

        # UI
        cv2.imshow("Autonomy & RViz View", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

except KeyboardInterrupt: pass

print("\n--- SHUTTING DOWN ---")
if arduino is not None:
    try:
        arduino.write(('x\n').encode())
        arduino.close()
    except: pass
cap.release()
cv2.destroyAllWindows()
ros_node.destroy_node()
rclpy.shutdown()
