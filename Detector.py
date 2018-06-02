from scipy.spatial import distance as dist
from imutils import face_utils
import numpy as np
import imutils
import dlib
import cv2
import time

class StopAssignments(Exception): pass

class Detector:
	def __init__(self, path="shape_predictor_68_face_landmarks.dat", EYE_AR_THRESH = 0.3, EYE_AR_CONSEC_FRAMES = 48):
		self.detector = dlib.get_frontal_face_detector()
		self.predictor = dlib.shape_predictor(path)
		(self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
		(self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
		self.EYE_AR_THRESH = EYE_AR_THRESH
		self.EYE_AR_CONSEC_FRAMES = EYE_AR_CONSEC_FRAMES
		self.COUNTER = 0
		self.ALARM_ON = False
		self.printMessage = False
		print("[INFO] loading facial landmark predictor")

	def eye_aspect_ratio(self, eye):
		A = dist.euclidean(eye[1], eye[5])
		B = dist.euclidean(eye[2], eye[4])
		C = dist.euclidean(eye[0], eye[3])
		
		return (A + B) / (2.0 * C)

	def get_biggest_rect(self, rects):
		rect = rects[0]
		for temp in rects:
			if rect.area() < temp.area():
				rect = temp
		return rect

	def detect_drowsiness(self, frame):

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		rects = self.detector(gray, 0)
		self.ALARM_ON = False

		if rects:
			rect =  self.get_biggest_rect(rects)
			shape = self.predictor(gray, rect)
			shape = face_utils.shape_to_np(shape)

			(x, y, w, h) = face_utils.rect_to_bb(rect)
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

			leftEye = shape[ self.lStart:self.lEnd]
			rightEye = shape[self.rStart:self.rEnd]
			leftEAR = self.eye_aspect_ratio( leftEye )
			rightEAR = self.eye_aspect_ratio( rightEye )

			ear = (leftEAR + rightEAR) / 2.0

			leftEyeHull = cv2.convexHull(leftEye)
			rightEyeHull = cv2.convexHull(rightEye)
			cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
			cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

			self.printMessage = True
			
			if ear < self.EYE_AR_THRESH:
				self.COUNTER += 1
				if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES and not self.ALARM_ON:
					self.ALARM_ON = True
					cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
			else:
				self.COUNTER = 0
				self.ALARM_ON = False
		else:
			if self.printMessage:
				print "[INFO] Face is not detected"
				self.printMessage = False

		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF

		if key == ord("q"):
			cv2.destroyAllWindows()
			raise StopAssignments

		return self.ALARM_ON
