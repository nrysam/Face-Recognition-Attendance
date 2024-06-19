from flask import Flask, render_template, Response
import cv2
import os
import face_recognition
import numpy as np
import pickle
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime, timedelta

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "facialattendancerecognition.appspot.com"
})

# Get reference to the storage bucket
bucket = storage.bucket()

def load_encodings(file_path):
    with open(file_path, 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    return encodeListKnownWithIds

# Load the encoding files
print("Loading Encode Files ...")
encodeListKnownWithIds1 = load_encodings('EncodeFile.p')
encodeListKnownWithIds2 = load_encodings('EncodeFile2.p')

# Unpack encoding lists and IDs
encodeListKnown1, Ids1 = encodeListKnownWithIds1
encodeListKnown2, Ids2 = encodeListKnownWithIds2

# Merge the encoding lists and IDs
encodeListKnown = encodeListKnown1 + encodeListKnown2
Ids = Ids1 + Ids2

print("Encode files Loaded!")

# Import the Background
try:
    imgBackground = cv2.imread('resources/background_image.png')
    if imgBackground is None:
        raise FileNotFoundError("Background image not found")
except Exception as e:
    print(f"Error loading background image: {e}")
    imgBackground = np.zeros((720, 1280, 3), dtype=np.uint8)  # Fallback to a black background

# Import the mode images into a list
folderModePath = 'resources/modes'
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Resizing the mode images
for i in range(len(imgModeList)):
    imgModeList[i] = cv2.resize(imgModeList[i], (504, 687))

# Initialize variables for face recognition mode and counter
modeType = 0
counter = 0

def generate_frames():
    global imgBackground
    cap2 = cv2.VideoCapture(1)
    if cap2.isOpened():
        print(f"Webcam with index 1 opened successfully")
        cap2.set(3, 640)
        cap2.set(4, 480)
    else:
        print(f"Webcam with index 1 failed to open")
        cap2.release()
        return

    global modeType, counter

    while True:
        success, img = cap2.read()

        if not success:
            print("Error: Could not read frame")
            break

        try:
            img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
            img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            print(f"Error resizing or converting image: {e}")
            continue

        face_current_frame = face_recognition.face_locations(img_small)
        encode_current_frame = face_recognition.face_encodings(img_small, face_current_frame)

        try:
            imgBackground[180:180+480, 46:46+640] = img
            imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]
        except Exception as e:
            print(f"Error placing image: {e}")
            continue

        if face_current_frame:
            for encodeFace, faceLoc in zip(encode_current_frame, face_current_frame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                face_distance = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(face_distance)

                if matches[matchIndex]:
                    y1, x2, y2, x1 = [val * 4 for val in faceLoc]
                    bbox = 46 + x1, 180 + y1, x2 - x1, y2 - y1
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    employee_id = Ids[matchIndex]

                    if counter == 0:
                        counter = 1
                        modeType = 1

            if counter != 0:
                if counter == 1:
                    employee_info = db.reference(f'Employees/{employee_id}').get()
                    print(employee_info)

                    blob = bucket.get_blob(f'images/{employee_id}.jpg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgEmployee = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    last_attendance_time = datetime.strptime(employee_info['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()
                    last_attendance_date = last_attendance_time.date()
                    current_date = current_time.date()

                    if last_attendance_date < current_date:
                        ref = db.reference(f'Employees/{employee_id}')
                        ref.child('last_attendance_time').set(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                        ref.child('attendance').child(current_date.strftime("%Y-%m-%d")).set({'clock_in': current_time.strftime("%H:%M:%S")})
                    else:
                        elapsed_hours = (current_time - last_attendance_time).total_seconds() / 3600
                        if elapsed_hours >= 9:
                            ref = db.reference(f'Employees/{employee_id}')
                            ref.child('attendance').child(last_attendance_date.strftime("%Y-%m-%d")).update({'clock_out': current_time.strftime("%H:%M:%S")})
                            employee_info['total_attendance'] += 1
                            ref.child('total_attendance').set(employee_info['total_attendance'])
                            ref.child('last_attendance_time').set(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            modeType = 3
                            counter = 0
                            imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2

                        imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

                    if counter <= 10:
                        (w, h), _ = cv2.getTextSize(employee_info['name'], cv2.FONT_HERSHEY_DUPLEX, 1, 1)
                        offset = (504-w)//2
                        cv2.putText(imgBackground, str(employee_info['name']), (750+offset, 470),
                                    cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 0), 2)
                        cv2.putText(imgBackground, str(employee_id), (1000, 528),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)
                        cv2.putText(imgBackground, str(employee_info['department']), (1000, 592),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)
                        cv2.putText(imgBackground, str(employee_info['total_attendance']), (795, 703),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)
                        cv2.putText(imgBackground, str(employee_info['year_joined']), (1145, 703),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)

                        imgBackground[171:171+233, 887:887+233] = imgEmployee
                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        employee_info = []
                        imgEmployee = []
                        imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

        else:
            modeType = 0
            counter = 0

        ret, buffer = cv2.imencode('.jpg', imgBackground)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap2.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
