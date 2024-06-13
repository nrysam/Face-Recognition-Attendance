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

def create_database_entry(employee_id, name, department, starting_year):
    data = {
        "name": name,
        "department": department,
        "starting_year": starting_year,
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
            resized_img = cv2.resize(img, (233, 233))
            file_name = f'Images/{employee_id}.jpg'
            cv2.imwrite(file_name, resized_img)
            break
    cap.release()
    cv2.destroyAllWindows()
    return file_name

def upload_to_storage(file_name):
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)

def encode_faces():
    folderPath = 'Images'
    pathList = os.listdir(folderPath)
    imgList = []
    Ids = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        Ids.append(os.path.splitext(path)[0])
    
    encodeList = []
    for img in imgList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    
    encodeListKnownWithIds = [encodeList, Ids]
    with open("EncodeFile2.p", 'wb') as file:
        pickle.dump(encodeListKnownWithIds, file)

def main():
    employee_id = input("Enter Employee ID: ")
    name = input("Enter Name: ")
    department = input("Enter Department: ")
    starting_year = int(input("Enter Starting Year: "))
    
    create_database_entry(employee_id, name, department, starting_year)
    file_name = capture_face(employee_id)
    upload_to_storage(file_name)
    encode_faces()
    print("Registration Complete")

if __name__ == "__main__":
    main()
