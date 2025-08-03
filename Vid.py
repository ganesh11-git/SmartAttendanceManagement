import os
import time
import face_recognition as fr
import cv2
import numpy as np
import csv
import pymysql
from datetime import datetime

# Face dataset and student list
faces_directory = "train/"
known_face_encodings = []
known_face_names = []

for filename in os.listdir(faces_directory):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        image_path = os.path.join(faces_directory, filename)
        image = fr.load_image_file(image_path)
        encodings = fr.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(filename)[0].capitalize())

# Attendance tracking
def run_attendance_period():
    students_present = set()
    students = known_face_names.copy()
    session_start_time = time.time()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H-%M-%S")
    csv_filename = f"{date}_{time_now}.csv"

    # Start video capture
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["roll_no", "periods_attended", "date"])

        print("Attendance session started...")

        while True:
            _, frame = video_capture.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = fr.face_locations(rgb_small_frame)
            face_encodings = fr.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = fr.compare_faces(known_face_encodings, face_encoding)
                face_distances = fr.face_distance(known_face_encodings, face_encoding)

                name = "Unknown"
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        if name not in students_present:
                            students_present.add(name)
                            writer.writerow([name, 1, date])
                            print(f"{name} marked present for 1 period.")

            cv2.imshow("Attendance", frame)

            if time.time() - session_start_time > 600:  # 1-minute session
                print("Session ended.")
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Session ended by user.")
                break

            time.sleep(1)

        video_capture.release()
        cv2.destroyAllWindows()

    # Update bunking and absentee files
    update_absentees_bunking(known_face_names, students_present, date)
    insert_to_mysql(csv_filename)

# Create or append to absentees and bunkers list
def update_absentees_bunking(known_names, present_set, date):
    absentees = list(set(known_names) - present_set)

    with open("absentees.csv", "a", newline="") as afile:
        writer = csv.writer(afile)
        writer.writerow([f"Date: {date}"])
        writer.writerows([[name] for name in absentees])

    with open("bunking.csv", "a", newline="") as bfile:
        writer = csv.writer(bfile)
        writer.writerow([f"Date: {date}"])
        writer.writerows([[name] for name in absentees])

# Load attendance data into MySQL
def insert_to_mysql(filename):
    try:
        conn = pymysql.connect(host="localhost", user="root", password="", database="attendance_db")
        cursor = conn.cursor()

        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cursor.execute(
                    "INSERT INTO attendance (roll_no, periods_attended, date) VALUES (%s, %s, %s)",
                    (row["roll_no"], int(row["periods_attended"]), row["date"])
                )

        conn.commit()
        cursor.close()
        conn.close()
        print("Attendance inserted into MySQL successfully.")

    except Exception as e:
        print("Database error:", e)

# Main loop for scheduled run
print("Waiting for start time...")
trigger_times = ["18:52", "10:00", "11:00", "14:00", "15:00"]  # You can customize period times

while True:
    current_time = datetime.now().strftime("%H:%M")
    if current_time in trigger_times:
        run_attendance_period()
        time.sleep(65)  # Ensure it doesn’t re-trigger within same minute
    time.sleep(10)
