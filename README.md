# Smart Patient Monitoring System 🩺

This project implements an IoT-based remote patient monitoring system using Raspberry Pi, sensors, and a cloud backend. It provides real-time updates on patient vitals such as SPO2, heart rate, and temperature using ThingSpeak, and a Flask-powered web interface to monitor patient status.

## Features

- Monitors patient vitals: **Heart Rate**, **SPO2**, **Temperature**
- Uses **ThingSpeak** for cloud data upload and analytics
- Alerts for **falls** (motion detection) and **emergency calls** (push button)
- Displays patient info using an **LCD**
- Captures images using **PiCamera** when fall detected
- Includes a **Flask dashboard** with routes to display:
  - Patient Info
  - In-Bed Status
  - Heart Rate and SPO2 (per patient)

## Hardware & Tools

- **Raspberry Pi** with RPi.GPIO
- **DHT11** for temperature/humidity
- **Ultrasonic Sensor** for bed detection
- **PiCamera** for video capture
- **LCD1602**, push buttons, buzzers, LEDs
- **RFID module** for patient ID
- **Flask** (Python web server)
- **ThingSpeak** (cloud logging)

## Routes (Flask Web App)

- `/` – Home page
- `/Patient_Info` – View all patients
- `/In_Bed` – Bed occupancy info
- `/HeartRate/<patientNo>` – Heart rate history
- `/SPO2/<patientNo>` – SPO2 history

## Getting Started

1. Clone this repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/smart-patient-monitoring.git
   cd smart-patient-monitoring
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the main script:
   ```bash
   python src/COE410_Project_Final_Code_thread.py
   ```

> 🛠️ Make sure to run on a Raspberry Pi with GPIO and peripherals connected.


*Created by Maria Boxwala – Integrating health-tech and IoT for real-world impact.*
