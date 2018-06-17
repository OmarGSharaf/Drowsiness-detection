from scipy.spatial import distance as dist
from imutils import face_utils
import numpy as np
import dlib
import cv2

class EyeDetector:
	def __init__(self, predictor = 'assets/shape_predictor_68_face_landmarks.dat'):

		self.predictor = dlib.shape_predictor(predictor)
		(self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
		(self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

	@staticmethod
	def eye_aspect_ratio(eye):
		# compute the euclidean distances between the two sets of
		# vertical eye landmarks (x, y)-coordinates
		A = dist.euclidean(eye[1], eye[5])
		B = dist.euclidean(eye[2], eye[4])

		# compute the euclidean distance between the horizontal
		# eye landmark (x, y)-coordinates
		C = dist.euclidean(eye[0], eye[3])

		# compute the eye aspect ratio
		ear = (A + B) / (2.0 * C)

		# return the eye aspect ratio
		return ear

	def get_eye(self, frame, facebox):

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		rect = dlib.rectangle(facebox[0], facebox[1], facebox[2], facebox[3])
		shape = self.predictor(gray, rect)
		shape = face_utils.shape_to_np(shape)

		# extract the left and right eye coordinates, then use the
		# coordinates to compute the eye aspect ratio for both eyes
		leftEye = shape[self.lStart:self.lEnd]
		rightEye = shape[self.rStart:self.rEnd]
		leftEAR = self.eye_aspect_ratio(leftEye)
		rightEAR = self.eye_aspect_ratio(rightEye)

		# average the eye aspect ratio together for both eyes
		ear = (leftEAR + rightEAR) / 2.0

		# compute the convex hull for the left and right eye, then
		# visualize each of the eyes
		leftEyeHull = cv2.convexHull(leftEye)
		rightEyeHull = cv2.convexHull(rightEye)
		cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
		cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
		
		return ear