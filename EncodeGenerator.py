import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket' : "facialattendancerecognition.appspot.com"
})


# Import people faces
folderPath = 'images'
pathList = os.listdir(folderPath)
print(pathList)

imgList = []
Ids = []

for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    Ids.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)
    
    # print(path)
    # print(os.path.splitext(path)[0])
print(Ids)


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    
    return encodeList

print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, Ids]
# print(encodeListKnown)
print("Encoding Complete")

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Saved")