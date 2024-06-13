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
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket' : "facialattendancerecognition.appspot.com"
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
imgBackground = cv2.imread('resources/background_image.png')

# Import the mode images into a list
folderModePath = 'resources/modes'
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))

# Resizing the mode images
for i in range(len(imgModeList)):
    imgModeList[i] = cv2.resize(imgModeList[i], (504, 687))

# Initialize variables for face recognition mode and counter
modeType = 0
counter = 0

# Setup the video capture
cap2 = cv2.VideoCapture(1) # Change the camera index here
if cap2.isOpened():
    print(f"Webcam with index 1 opened successfully")
    cap2.set(3, 640)
    cap2.set(4, 480)
else:
    print(f"Webcam with index 1 failed to open")
    cap2.release()

while True:
    success, img = cap2.read()

    if not success:
        print("Error: Could not read frame")
        break

    try:
        # Resize and convert the image to RGB
        img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
        img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
    except cv2.error as e:
        print(f"Error resizing or converting image: {e}")
        continue

    # Detect face locations and encodings in the current frame
    face_current_frame = face_recognition.face_locations(img_small)
    encode_current_frame = face_recognition.face_encodings(img_small, face_current_frame)
    
    # Overlay the webcam image onto the background
    imgBackground[180:180+480, 46:46+640] = img
    imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

    if face_current_frame:
        for encodeFace, faceLoc in zip(encode_current_frame, face_current_frame):
            # Compare face encodings with known encodings
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            face_distance = face_recognition.face_distance(encodeListKnown, encodeFace)

            # Find the best match
            matchIndex = np.argmin(face_distance)
            
            if matches[matchIndex]:
                y1, x2, y2, x1 = [val * 4 for val in faceLoc]
                bbox = 46 + x1, 180 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                employee_id = Ids[matchIndex]
                
                if counter == 0 :
                    counter = 1 
                    modeType = 1
        if counter != 0:

            if counter == 1 :
                # # Get employee data from the database
                employee_info = db.reference(f'Employees/{employee_id}').get()
                print(employee_info)

                # Get the Employee Images from the storage
                blob = bucket.get_blob(f'Images/{employee_id}.jpg')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgEmployee = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                # Update attendance data
                datetimeObject = datetime.strptime(employee_info['last_attendance_time'],
                                                "%Y-%m-%d %H:%M:%S")
                
                secondsElapsed = (datetime.now()-datetimeObject).total_seconds()
                print(secondsElapsed)

                if secondsElapsed > 60 :
                    ref = db.reference(f'Employees/{employee_id}')
                    employee_info['total_attendance'] +=1
                    ref.child('total_attendance').set(employee_info['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else :
                    modeType = 3
                    counter = 0
                    imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]
            
            if modeType !=3 :
                if 10 < counter < 20:
                    modeType = 2

                    imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

                if counter <= 10:
                    # Display employee details
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
                    cv2.putText(imgBackground, str(employee_info['starting_year']), (1145, 703),
                                cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)
                
                    imgBackground[171:171+233, 887:887+233] = imgEmployee
                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    employee_info=[]
                    imgEmployee = []
                    imgBackground[33:33+696, 740:740+504] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    # Display the resulting frame
    cv2.imshow("Face Recognition Attendance", imgBackground)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and destroy all windows
cap2.release()
cv2.destroyAllWindows()