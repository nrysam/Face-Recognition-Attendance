import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"https://facialattendancerecognition-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Employees')

data = {
    "100200":
        {  
            "name" : "Ana de Armas",
            "department" : "Sales",
            "year_joined" : 2023,
            "total_attendance" : 20,
            "last_attendance_time" : "2023-12-10 07:44:22"
        },
    "123456":
        {  
            "name" : "Elon Musk",
            "department" : "Engineer",
            "year_joined" : 2022,
            "total_attendance" : 140,
            "last_attendance_time" : "2024-04-22 06:44:22"
        },
    "198765":
        {  
            "name" : "Rihanna",
            "department" : "Marketing",
            "year_joined" : 2022,
            "total_attendance" : 80,
            "last_attendance_time" : "2024-02-10 12:44:22"
        },
    "220212":
        {  
            "name" : "David Beckham",
            "department" : "People Development",
            "year_joined" : 2023,
            "total_attendance" : 75,
            "last_attendance_time" : "2024-04-24 07:44:22"
        }
}

for key, value in data.items():
    ref.child(key).set(value)