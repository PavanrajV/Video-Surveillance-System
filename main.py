from core.camera import Camera
from core.motion_detector import MotionDetector
from core.recorder import Recorder
from core.alerts import play_alert
from core.database import log_event
from ui.dashboard import Dashboard

camera = Camera()
detector = MotionDetector()
recorder = Recorder()

motion_timer = 0

def update():

    global motion_timer

    frame = camera.get_frame()
    if frame is None:
        return None

    frame, motion, area = detector.detect(frame)

    if motion:
        recorder.start()
        recorder.write(frame)
        log_event(area)
        play_alert()
        motion_timer = 30

    else:
        motion_timer -= 1
        if motion_timer <= 0:
            recorder.stop()

    return frame

app = Dashboard(update)
app.mainloop()

camera.release()