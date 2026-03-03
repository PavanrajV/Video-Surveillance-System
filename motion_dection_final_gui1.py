import cv2
import numpy as np
import os
import time
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, filedialog
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

def preprocess_frame(frame, prev_frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    if prev_frame is None:
        return gray, None
    diff = cv2.absdiff(prev_frame, gray)
    _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)
    return gray, thresh

def detect_motion(thresh, min_area=800):
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [(cv2.boundingRect(contour)) for contour in contours if cv2.contourArea(contour) > min_area]
    return boxes

def open_video():
    filename = filedialog.askopenfilename(initialdir="C:/motion_video", title="Select Video", filetypes=(("AVI files", "*.avi"), ("All files", "*.*")))
    if filename:
        try:
            os.startfile(filename)
        except AttributeError:
            import subprocess
            subprocess.call(["xdg-open", filename])

def capture_snapshot():
    global cap
    if cap is not None and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            snapshot_filename = os.path.join("C:/motion_video", f"snapshot_{int(time.time())}.jpg")
            cv2.imwrite(snapshot_filename, frame)
            print(f"Snapshot saved: {snapshot_filename}")

def toggle_dark_mode():
    current_bg = root.cget("bg")
    new_bg = "black" if current_bg == "white" else "white"
    root.configure(bg=new_bg)

def update_video_feed():
    global prev_frame, recording, out, frames_after_motion, cap, update_task
    if cap is None or not cap.isOpened():
        return
    ret, frame = cap.read()
    if not ret:
        return
    prev_frame, thresh = preprocess_frame(frame, prev_frame)
    if thresh is not None:
        motion_boxes = detect_motion(thresh, motion_sensitivity.get())
        motion_intensity = min(len(motion_boxes) * 20, 100)
        motion_history.append(motion_intensity)
        for (x, y, w, h) in motion_boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if motion_boxes:
            frames_after_motion = buffer_frames.get()
            if not recording:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                video_filename = os.path.join(save_path, f"motion_{timestamp}.avi")
                out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
                recording = True
        else:
            if frames_after_motion > 0:
                frames_after_motion -= 1
            else:
                if recording:
                    out.release()
                    recording = False
        if recording and out is not None:
            out.write(frame)
    line.set_ydata(list(motion_history))
    fig.canvas.draw()
    fig.canvas.flush_events()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    img = ImageTk.PhotoImage(img)
    video_label.img = img  # Prevent garbage collection
    video_label.config(image=img)
    update_task = video_label.after(10, update_video_feed)

def stop_detection():
    global cap, update_task
    if cap is not None:
        cap.release()
        cap = None
    if update_task is not None:
        video_label.after_cancel(update_task)
        update_task = None

def start_detection():
    global cap, prev_frame
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    prev_frame = None
    update_video_feed()

def main():
    global cap, prev_frame, recording, out, buffer_frames, motion_history, save_path, fourcc, fig, ax, line, video_label, motion_sensitivity, frames_after_motion, update_task, root
    cap = None
    prev_frame = None
    save_path = "C:/motion_video"
    os.makedirs(save_path, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    recording = False
    out = None
    frames_after_motion = 0
    update_task = None
    root = tk.Tk()
    root.title("Motion Detection System")
    root.geometry("1200x800")
    root.resizable(True, True)
    
    motion_sensitivity = tk.IntVar(value=800)
    buffer_frames = tk.IntVar(value=100)
    
    video_label = tk.Label(root)
    video_label.grid(row=0, column=0, padx=10, pady=10, sticky='nw')
    
    fig, ax = plt.subplots()
    fig.tight_layout()

    motion_history = deque([0] * 50, maxlen=50)
    line, = ax.plot(range(50), motion_history, label="Motion Intensity")
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 50)
    ax.set_xlabel("Time")
    ax.set_ylabel("Intensity (%)")
    ax.set_title("Motion Intensity Over Time")
    ax.legend()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky='sw')
    
    control_frame = ttk.Frame(root)
    control_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky='ne')
    
    start_button = ttk.Button(control_frame, text="Start Detection", command=start_detection)
    start_button.pack(pady=5)
    stop_button = ttk.Button(control_frame, text="Stop Detection", command=stop_detection)
    stop_button.pack(pady=5)
    snapshot_button = ttk.Button(control_frame, text="Capture Snapshot", command=capture_snapshot)
    snapshot_button.pack(pady=5)
    open_video_button = ttk.Button(control_frame, text="View Recorded Videos", command=open_video)
    open_video_button.pack(pady=5)
    dark_mode_button = ttk.Button(control_frame, text="Toggle Dark Mode", command=toggle_dark_mode)
    dark_mode_button.pack(pady=5)
    root.protocol("WM_DELETE_WINDOW", stop_detection)
    root.mainloop()

if __name__ == "__main__":
    main()
