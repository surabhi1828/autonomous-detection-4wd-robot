// --- SPEED PINS (PWM) ---
const int left_RPWM = 5;  
const int left_LPWM = 6;  
const int right_RPWM = 9; 
const int right_LPWM = 10;

// --- WAKE UP PINS (Enable) ---
const int left_REN = 7;
const int left_LEN = 8;
const int right_REN = 11;
const int right_LEN = 12;

// --- EXTREMELY SLOW SPEED ---
int speed = 50; // Absolute minimum torque threshold
unsigned long lastCmdTime = 0; // Safety timer memory

void setup() {
  Serial.begin(9600);
  
  pinMode(left_RPWM, OUTPUT); pinMode(left_LPWM, OUTPUT);
  pinMode(right_RPWM, OUTPUT); pinMode(right_LPWM, OUTPUT);
  pinMode(left_REN, OUTPUT); pinMode(left_LEN, OUTPUT);
  pinMode(right_REN, OUTPUT); pinMode(right_LEN, OUTPUT);

  // Keep the drivers awake and ready
  digitalWrite(left_REN, HIGH); digitalWrite(left_LEN, HIGH);
  digitalWrite(right_REN, HIGH); digitalWrite(right_LEN, HIGH);

  Serial.println("Muscle System Live. 60ms Micro-burst active.");
  Serial.println("Debugging Enabled: Waiting for commands...");
}

void loop() {
  // 1. Listen for commands from the Python/ROS 2 Node or Serial Monitor
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    // Filter out hidden newline/carriage return characters from the Serial Monitor
    if (cmd != '\n' && cmd != '\r') {
      
      // THE DEBUG ECHO: Print exactly what we just received
      Serial.print("DEBUG - Command Received: ");
      Serial.println(cmd);
      
      lastCmdTime = millis(); // Reset the deadman timer
      
      if (cmd == 'w') { // Forward
        analogWrite(left_RPWM, speed); analogWrite(left_LPWM, 0);
        analogWrite(right_RPWM, speed); analogWrite(right_LPWM, 0);
      } 
      else if (cmd == 's') { // Backward
        analogWrite(left_RPWM, 0); analogWrite(left_LPWM, speed);
        analogWrite(right_RPWM, 0); analogWrite(right_LPWM, speed);
      }
      else if (cmd == 'a') { // Turn Left
        analogWrite(left_RPWM, 0); analogWrite(left_LPWM, speed);
        analogWrite(right_RPWM, speed); analogWrite(right_LPWM, 0);
      }
      else if (cmd == 'd') { // Turn Right
        analogWrite(left_RPWM, speed); analogWrite(left_LPWM, 0);
        analogWrite(right_RPWM, 0); analogWrite(right_LPWM, speed);
      }
      else if (cmd == 'x') { // Explicit Stop
        analogWrite(left_RPWM, 0); analogWrite(left_LPWM, 0);
        analogWrite(right_RPWM, 0); analogWrite(right_LPWM, 0);
      }
    }
  }

  // 2. THE DEADMAN SWITCH (Micro-Burst)
  // If 60 milliseconds pass without a new command, instantly kill the motors.
  if (millis() - lastCmdTime > 1000) {
      analogWrite(left_RPWM, 0); analogWrite(left_LPWM, 0);
      analogWrite(right_RPWM, 0); analogWrite(right_LPWM, 0);
  }
}