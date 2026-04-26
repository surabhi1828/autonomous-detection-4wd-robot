# Dual-Pipeline Visual Servoing & Odometry for 4WD Robots

### Academic Context
* **Course:** Mobile and Autonomous Robots (UE23CS343BB7)
* **Institution:** PES University
* **Instructor:** Dr. Adithya Balasubramanyam
* **Team Members:** Surabhi Venkatesha, Mahika Neranjen, Brinda S, B M Krupa

🎥 **[Click Here to View the Final Demonstration Video](INSERT_YOUR_VIDEO_LINK_HERE)**

---

## Overview
This repository contains the software architecture for an autonomous 4WD differential-drive robot. It utilizes a distributed edge-computing framework via ROS 2. The system features two parallel pipelines processing a monocular IP-camera stream:
1. **Reactive Visual Servoing:** Dynamically tracks a high-intensity target (calibrated for flame/green objects) using HSV color space masking to issue proportional steering commands.
2. **Visual Odometry:** Utilizes Lucas-Kanade sparse optical flow to estimate spatial movement and publish a qualitative trajectory to the ROS 2 network.

## Hardware Architecture
* **Processing Node:** Ubuntu Linux host running Python 3 & ROS 2 
* **Microcontroller:** Arduino (acting as the low-level motor hardware driver)
* **Motor Driver:** Dual-channel high-current driver
* **Actuators:** 4x High-Torque DC Motors (wired in parallel for Left/Right differential control)
* **Sensor:** Smartphone camera streaming over Wi-Fi TCP/IP bridge

## Repository Contents
* `visual_slam.py`: The master ROS 2 node handling OpenCV processing, target tracking logic, and PySerial communication.
* `robot-movement.ino`: The C++ Arduino firmware featuring PWM motor control and a 1000ms safety deadman switch to prevent runaway states.
* `cali_flame.py`: A custom diagnostic GUI tool for real-time HSV threshold tuning to mitigate environmental glare and overexposure.

## Prerequisites
* ROS 2 (Humble/Iron) installed and sourced.
* Python dependencies installed via: 
  ```bash
  pip install -r requirements.txt
  ```
## Execution Protocol
* Flash robot-movement.ino into the Arduino and connect it to the host via USB (/dev/ttyACM0).

* Start the IP Camera stream on the smartphone and ensure the URL matches the one in visual_slam.py.

* Open Terminal 1 and launch RViz2:

```bash
rviz2
```
(Set fixed frame to odom and add Path topic /robot_path)

* Open Terminal 2 and launch the autonomous node:

``` bash
python3 visual_slam.py
```
