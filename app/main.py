import face_recognition
import cv2
import numpy as np
import mysql.connector
from datetime import datetime, timedelta

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="your_username",
    password="your_password",
    database="facial_recognition"
)
cursor = db.cursor()

# Function to insert face encoding into the database
def insert_face(name, encoding):
    sql = "INSERT INTO faces (name, encoding) VALUES (%s, %s)"
    val = (name, encoding.tobytes())
    cursor.execute(sql, val)
    db.commit()

# Function to fetch all face encodings from the database
def fetch_all_faces():
    cursor.execute("SELECT name, encoding FROM faces")
    result = cursor.fetchall()
    known_face_encodings = []
    known_face_names = []
    for row in result:
        name, encoding = row
        known_face_names.append(name)
        known_face_encodings.append(np.frombuffer(encoding, dtype=np.float64))
    return known_face_names, known_face_encodings

# Function to perform reverse image lookup
def reverse_image_lookup(face_encoding):
    known_face_names, known_face_encodings = fetch_all_faces()
    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
    name = "Unknown"
    if True in matches:
        first_match_index = matches.index(True)
        name = known_face_names[first_match_index]
    return name

# Main function for facial recognition
def facial_recognition():
    video_capture = cv2.VideoCapture(0)

    known_face_names, known_face_encodings = fetch_all_faces()

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    last_seen = {}

    while True:
        ret, frame = video_capture.read()

        if process_this_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                name = reverse_image_lookup(face_encoding)

                if name == "Unknown":
                    name = "Unknown"
                else:
                    if name in last_seen:
                        if datetime.now() - last_seen[name] > timedelta(minutes=15):
                            print(f"Performing reverse image lookup for {name}")
                            # Perform reverse image lookup logic here
                            # This could involve querying an external API or another database
                    last_seen[name] = datetime.now()

                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    facial_recognition()