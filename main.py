import cv2
import csv
import os

# Initialize webcam
cap = cv2.VideoCapture(0)
qr_detector = cv2.QRCodeDetector()

print("Camera initialized. Show QR codes... Press 'q' to quit.")

seen_data = set()
csv_filename = "output.csv"

# Create output.csv with headers if it doesn't exist
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name Card ID', 'Last Name', 'First Name', 'School', 'Session'])

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    try:
        data, bbox, _ = qr_detector.detectAndDecode(frame)
    except cv2.error as e:
        print(f"OpenCV QR decode error: {e}")
        data = None
        bbox = None

    if data and data not in seen_data:
        data = str(data)
        print(data)
        seen_data.add(data)

        fields = data.strip().split(',')
        if len(fields) == 5:
            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(fields)
        else:
            print(f"Skipped malformed data: {data}")

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
