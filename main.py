import cv2
import csv
import os
import pygame
import sys
import tkinter as tk
from tkinter import filedialog
from collections import Counter

# Setup tkinter for file dialogs
tk.Tk().withdraw()

# Initialize Pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("QR Code Scanner UI")
font = pygame.font.SysFont("Arial", 24)
clock = pygame.time.Clock()

# Sound Defaults
beep_path = "beep.wav"
error_path = "error-10.wav"

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None

beep = load_sound(beep_path)
error_sound = load_sound(error_path)

# OpenCV QR Setup
cap = cv2.VideoCapture(0)
qr_detector = cv2.QRCodeDetector()

# State
seen_data = set()
first_letter_counts = Counter()
error_count = 0
csv_file = "output.csv"
scan_log = []
scroll_offset = 0
max_scroll = 0
scroll_speed = 20

# Create CSV if missing
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name Card ID', 'Last Name', 'First Name', 'School', 'Session'])

# Button Helper
def draw_button(text, x, y, w, h, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    color = (70, 130, 180) if x+w > mouse[0] > x and y+h > mouse[1] > y else (100, 100, 100)
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=8)
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, (x + 10, y + 10))
    if click[0] == 1 and x+w > mouse[0] > x and y+h > mouse[1] > y:
        pygame.time.wait(200)
        if action:
            action()

# Button Actions
def select_csv_file():
    global csv_file
    path = filedialog.asksaveasfilename(defaultextension=".csv")
    if path:
        csv_file = path

def export_csv():
    try:
        dest = filedialog.asksaveasfilename(defaultextension=".csv")
        if dest:
            with open(csv_file, 'r') as src, open(dest, 'w', newline='') as dst:
                dst.write(src.read())
    except Exception as e:
        print("Export failed:", e)

def select_beep_sound():
    global beep
    path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if path:
        beep = load_sound(path)

def select_error_sound():
    global error_sound
    path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if path:
        error_sound = load_sound(path)

def reset_counters():
    seen_data.clear()
    first_letter_counts.clear()
    scan_log.clear()
    global error_count, scroll_offset
    error_count = 0
    scroll_offset = 0

# Main Loop
running = True
while running:
    screen.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            scroll_offset -= event.y * scroll_speed
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                scroll_offset += scroll_speed
            elif event.key == pygame.K_DOWN:
                scroll_offset -= scroll_speed

    ret, frame = cap.read()
    if not ret:
        print("\u274c Failed to grab frame.")
        if error_sound:
            error_sound.play()
        error_count += 1
        continue

    data, bbox, _ = qr_detector.detectAndDecode(frame)
    if data and data not in seen_data:
        data = str(data)
        seen_data.add(data)
        fields = data.strip().split(',')
        if len(fields) == 5:
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(fields)
            scan_log.append(data)
            if beep:
                beep.play()
        else:
            error_count += 1
            if error_sound:
                error_sound.play()

    if bbox is not None and len(bbox) > 0:
        for i in range(len(bbox)):
            pt1 = tuple(map(int, bbox[i][0]))
            pt2 = tuple(map(int, bbox[(i+1) % len(bbox)][0]))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

    # Render frame to pygame
    frame = cv2.resize(frame, (500, 375))
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
    screen.blit(frame_surface, (30, 30))

    # Buttons
    draw_button("Select CSV File", 600, 30, 200, 40, select_csv_file)
    draw_button("Export CSV", 600, 80, 200, 40, export_csv)
    draw_button("Select Beep Sound", 600, 130, 200, 40, select_beep_sound)
    draw_button("Select Error Sound", 600, 180, 200, 40, select_error_sound)
    draw_button("Reset Counters", 600, 230, 200, 40, reset_counters)

    # Stats
    scan_text = font.render(f"Scanned: {len(seen_data)}", True, (255, 255, 255))
    screen.blit(scan_text, (600, 300))

    error_text = font.render(f"Errors: {error_count}", True, (255, 100, 100))
    screen.blit(error_text, (600, 340))

    y = 380
    for letter, count in sorted(first_letter_counts.items()):
        text = font.render(f"{letter}: {count}", True, (200, 200, 100))
        screen.blit(text, (600, y))
        y += 30

    # Scrollable log panel
    log_area = pygame.Rect(30, 430, 940, 240)
    pygame.draw.rect(screen, (50, 50, 50), log_area)
    pygame.draw.rect(screen, (100, 100, 100), log_area, 2)

    combined_log = ["Recent Scans:"] + [f"\u2714 {entry}" for entry in scan_log]
    max_scroll = max(0, len(combined_log) * 28 - log_area.height)

    # ✅ Clamp scroll_offset
    scroll_offset = max(0, min(scroll_offset, max_scroll))

    surface_log = pygame.Surface((log_area.width, len(combined_log) * 28), pygame.SRCALPHA)
    surface_log.fill((0, 0, 0, 0))

    for i, entry in enumerate(combined_log):
        color = (200, 255, 200) if entry.startswith("\u2714") else (255, 150, 150) if entry.startswith("\u2718") else (255, 255, 255)
        entry_text = font.render(entry, True, color)
        surface_log.blit(entry_text, (10, i * 28))

    screen.blit(surface_log, log_area.topleft, area=pygame.Rect(0, scroll_offset, log_area.width, log_area.height))

    pygame.display.flip()
    clock.tick(30)

# Cleanup
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
