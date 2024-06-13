# Face Recognition Attendance System
This project implements a face recognition attendance system using OpenCV, Face Recognition library, and Firebase. The system allows for face registration, encoding of faces, and real-time attendance tracking.

## Table of Contents
- [Introduction](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Introduction)
- [Features](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Features)
- [Requirements](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Requirements)
- [Installation](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Installation)
- [Usage](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Usages)
- [File Descriptions](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#File_Description)
- [Acknowledgments](https://github.com/nrysam/Face-Recognition-Attendance/blob/main/README.md#Acknowledgements)

## Introduction
The Face Recognition Attendance System is designed to automate attendance tracking using facial recognition technology. This system captures images, processes them to extract facial features, and stores them in a database. During attendance, it identifies the faces in the video feed and updates the attendance records accordingly.

## Features
- Face Registration
- Face Encoding
- Real-Time Attendance Tracking
- Firebase Integration for Database and Storage

## Requirements
- Python 3.6 or above
- OpenCV
- face_recognition
- numpy
- firebase_admin
- cvzone

## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

**2. Create a virtual environment and activate it:**

```bat
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

**3. Install the required packages:**

```bat
pip install -r requirements.txt
```

**4. Set up Firebase:**

- Download your Firebase project's serviceAccountKey.json and place it in the root directory of the project.
- Ensure your Firebase Realtime Database and Storage are correctly configured.

## Usage
**1. Database Initialization**

Create the initial database with employee details by running:

```bat
python DatabaseUpdate.py
```

**2. Face Registration**

Register new faces to the system by running:

```python
python face_registration.py
```

Follow the prompts to input employee details and capture their images.


**3. Generate Encodings**

Generate face encodings for the registered faces by running:

```bat
python EncodeGenerator.py
```

**4. Real-Time Attendance Tracking**

Start the real-time attendance tracking system by running:

```bat
python facial_recognition_attendance.py
```

## File Descriptions
- **facial_recognition_attendance.py**: Main script for real-time attendance tracking.
- **EncodeGenerator.py**: Script to encode images and store the encodings in Firebase.
- **DatabaseUpdate.p**y: Script to initialize the Firebase database with employee details.
- **face_registration.py**: Script for face registration, capturing images, and saving data to Firebase.

## Acknowledgements
- OpenCV
- face_recognition
- Firebase
