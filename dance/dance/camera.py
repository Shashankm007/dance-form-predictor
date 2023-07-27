import cv2
from model import DanceModel
import numpy as np

body_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_upperbody.xml")
print(body_classifier)
model = DanceModel("model.json", "model_weights.h5")
font = cv2.FONT_HERSHEY_SIMPLEX

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture("/root/Desktop/dance/bn.mp4")

    def __del__(self):
        self.video.release()

    # returns camera frames along with bounding boxes and predictions
    def get_frame(self):
        _, fr = self.video.read()
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        bodies = body_classifier.detectMultiScale(rgb, 1.3, 5)
        fc = rgb
        roi = cv2.resize(fc, (150, 150))
        print(roi[np.newaxis, :, :, np.newaxis].shape)
        pred = model.predict_dance(roi[np.newaxis])
        print(pred)
        

        _, jpeg = cv2.imencode('.jpg', fr)
        return jpeg.tobytes()
