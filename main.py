import cv2
import csv
import os
import pygame
from collections import Counter

# --- Initialize Pygame mixer for sound playback ---
pygame.mixer.init()
beep_sound_path = os.path.join(os.path.dirname(__file__), "beep.wav")

# Load the beep sound
try:
    beep = pygame.mixer.Sound(beep_sound_path)
except pygame.error as e:
    print(f"⚠️ Failed to load sound: {e}")
    beep = None

# --- Initialize webcam and QR code detector ---
cap = cv2.VideoCapture(0)
qr_detector = cv2.QRCodeDetector()

print("📷 Camera initialized. Show QR codes... Press 'q' to quit.")

seen_data = set()
first_letter_counts = Counter()
csv_filename = "output.csv"

# Create output.csv with headers if it doesn't exist
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name Card ID', 'Last Name', 'First Name', 'School', 'Session'])

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    try:
        data, bbox, _ = qr_detector.detectAndDecode(frame)
    except cv2.error as e:
        print(f"⚠️ OpenCV QR decode error: {e}")
        data = None
        bbox = None

    if data and data not in seen_data:
        data = str(data)
        print(data)
        seen_data.add(data)

        fields = data.strip().split(',')
        if len(fields) == 5:
            last_name = fields[1].strip()
            if last_name:
                first_char = last_name[0].upper()
                if first_char.isalpha():
                    first_letter_counts[first_char] += 1

            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(fields)

            if beep:
                beep.play()
        else:
            print(f"⚠️ Skipped malformed data: {data}")

    # Draw QR bounding box (optional)
    if bbox is not None and len(bbox) > 0:
        n = len(bbox)
        for i in range(n):
            pt1 = tuple(map(int, bbox[i][0]))
            pt2 = tuple(map(int, bbox[(i + 1) % n][0]))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

    # Display total scan count
    cv2.putText(frame, f"Scanned: {len(seen_data)}",
                (frame.shape[1] - 200, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 255), 2)

    # Display top 5 first-letter frequencies from Last Names
    top_first_letters = first_letter_counts.most_common(5)
    for i, (char, count) in enumerate(top_first_letters):
        text = f"{char}: {count}"
        cv2.putText(frame, text,
                    (frame.shape[1] - 200, 60 + (i * 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 200, 100), 2)

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
