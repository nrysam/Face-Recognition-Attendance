import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "facialattendancerecognition.appspot.com"
})

# Initialize the database reference
ref = db.reference('Employees')
bucket = storage.bucket()

def create_database_entry(employee_id, name, department, year_joined):
    data = {
        "name": name,
        "department": department,
        "year_joined": year_joined,
        "total_attendance": 0,
        "last_attendance_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    ref.child(employee_id).set(data)
    return data

def capture_face(employee_id):
    cap = cv2.VideoCapture(1)
    cap.set(3, 960)
    cap.set(4, 720)
    while True:
        success, img = cap.read()
        cv2.imshow('Face Registration', img)
        if cv2.waitKey(1) & 0xFF == ord('s'):
            # Allow user to crop the face manually
            r = cv2.selectROI('Face Registration', img, fromCenter=False)
            cropped_img = img[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
            resized_img = cv2.resize(cropped_img, (233, 233))
            file_name = f'images/{employee_id}.jpg'
            cv2.imwrite(file_name, resized_img)
            break
    cap.release()
    cv2.destroyAllWindows()
    return file_name

def upload_to_storage(file_name):
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)

def encode_face(file_name, employee_id):
    img = cv2.imread(file_name)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    encode = face_recognition.face_encodings(img)[0]
    encodeListKnownWithIds = [[encode], [employee_id]]
    with open("EncodeFile2.p", 'wb') as file:
        pickle.dump(encodeListKnownWithIds, file)

def main():
    employee_id = input("Enter Employee ID: ")
    name = input("Enter Name: ")
    department = input("Enter Department: ")
    year_joined = int(input("Enter Year Joined: "))
    
    create_database_entry(employee_id, name, department, year_joined)
    file_name = capture_face(employee_id)
    upload_to_storage(file_name)
    encode_face(file_name, employee_id)
    print("Registration Complete")

if __name__ == "__main__":
    main()