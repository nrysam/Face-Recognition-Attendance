import streamlit as st
import cv2
import os
import face_recognition
import numpy as np
import pickle
import cvzone
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime
import json

# Load the service account key from Streamlit secrets
service_account_info = st.secrets["gcp_service_account"]

# Parse the string back to JSON
service_account_info = json.loads(service_account_info)

# Initialize Firebase
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "facialattendancerecognition.appspot.com"
})

# Load Encodings
def load_encodings(file_path):
    with open(file_path, 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    return encodeListKnownWithIds

encodeListKnownWithIds1 = load_encodings('EncodeFile.p')
encodeListKnownWithIds2 = load_encodings('EncodeFile2.p')
encodeListKnown = encodeListKnownWithIds1[0] + encodeListKnownWithIds2[0]
Ids = encodeListKnownWithIds1[1] + encodeListKnownWithIds2[1]

# Streamlit App
st.title("Face Recognition Attendance System")

# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.selectbox("Choose an option", ("Face Registration", "Face Recognition Attendance"))

if option == "Face Registration":
    st.header("Face Registration")
    name = st.text_input("Name")
    employee_id = st.text_input("Employee ID")
    starting_year = st.number_input("Starting Year", min_value=1900, max_value=2100)
    department = st.text_input("Department")

    if st.button("Register and Capture"):
        cap = cv2.VideoCapture(0)
        cap.set(3, 233)
        cap.set(4, 233)

        st.write("Capturing image... Press 's' to save the image.")

        while True:
            success, img = cap.read()
            if not success:
                st.write("Failed to capture image.")
                break

            cv2.imshow('Face Registration', img)

            if cv2.waitKey(1) & 0xFF == ord('s'):
                img_path = f'Images/{employee_id}.jpg'
                cv2.imwrite(img_path, img)
                st.write(f"Image saved as {img_path}")
                break

        cap.release()
        cv2.destroyAllWindows()

        # Save to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(img_path)
        blob.upload_from_filename(img_path)

        # Update Firebase Database
        ref = db.reference('Employees')
        ref.child(employee_id).set({
            "name": name,
            "department": department,
            "starting_year": starting_year,
            "total_attendance": 0,
            "last_attendance_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        st.write("Registration successful!")

        # Encode the image
        img = face_recognition.load_image_file(img_path)
        img_encoding = face_recognition.face_encodings(img)[0]
        with open("EncodeFile2.p", 'wb') as file:
            encodeListKnownWithIds2[0].append(img_encoding)
            encodeListKnownWithIds2[1].append(employee_id)
            pickle.dump(encodeListKnownWithIds2, file)

        st.write("Face encoding saved!")

elif option == "Face Recognition Attendance":
    st.header("Face Recognition Attendance")
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    st.write("Running face recognition... Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            st.write("Failed to capture image.")
            break

        img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
        img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

        face_current_frame = face_recognition.face_locations(img_small)
        encode_current_frame = face_recognition.face_encodings(img_small, face_current_frame)

        for encodeFace, faceLoc in zip(encode_current_frame, face_current_frame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            face_distance = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(face_distance)

            if matches[matchIndex]:
                employee_id = Ids[matchIndex]
                employee_info = db.reference(f'Employees/{employee_id}').get()

                datetimeObject = datetime.strptime(employee_info['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()

                if secondsElapsed > 60:
                    ref = db.reference(f'Employees/{employee_id}')
                    employee_info['total_attendance'] += 1
                    ref.child('total_attendance').set(employee_info['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                st.write(f"Welcome {employee_info['name']} from {employee_info['department']}!")

        cv2.imshow("Face Recognition Attendance", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
