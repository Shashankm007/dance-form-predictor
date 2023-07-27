import cv2
from flask import render_template, url_for, flash, redirect, request, Response, current_app
from minor.model import DanceModel
import numpy as np
body_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_upperbody.xml")
print(body_classifier)
model = DanceModel("./model.json", "./model_weights.h5")
font = cv2.FONT_HERSHEY_SIMPLEX


class VideoCamera(object):
    def __init__(self, file_name):
        self.video = cv2.VideoCapture("./uploads/"+file_name)
        self.prediction = []
        self.totalFrames = 0

    def count_frames_manual(self):
        total = 0
        while True:
            (grabbed, frame) = self.video.read()
            if not grabbed:
                break
            total += 1
        self.totalFrames = total
        return self.totalFrames

    def __del__(self):
        self.video.release()

    # returns camera frames along with bounding boxes and predictions
    def get_frame(self, frames):
        _, fr = self.video.read()
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        bodies = body_classifier.detectMultiScale(rgb, 1.3, 5)
        fc = rgb
        roi = cv2.resize(fc, (150, 150))
        #print(roi[np.newaxis, :, :, np.newaxis].shape)
        pred = model.predict_dance(roi[np.newaxis])
        self.prediction.append(pred)
        # print(self.prediction)
        _, jpeg = cv2.imencode('.jpg', fr)
        return jpeg.tobytes(), self.prediction
