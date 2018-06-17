import cv2, playsound, time, numpy as np
from multiprocessing import Process, Queue
from threading import Thread
from OpSystemDetector import detectOpSystem
from FaceDetector import FaceDetector
from EyeDetector import EyeDetector
from MarkDetector import MarkDetector
from PoseEstimator import PoseEstimator
from Videofeed import Videofeed

# multiprocessing may not work on Windows and macOS, check OS for safety.
detectOpSystem()

CNN_INPUT_SIZE = 128

class Detector:
    def __init__(self, EYE_AR_THRESH = 0.3, ROLL_THRESH = 20, TIME_THRESH = 10):
        
        self.EYE_AR_THRESH = EYE_AR_THRESH
        self.ROLL_THRESH = ROLL_THRESH
        self.TIME_THRESH = TIME_THRESH
        self.T1 = None
        self.T2 = None

        self.videofeed = Videofeed()
        self.videofeed.start()
        frame = self.videofeed.get_frame()

        self.faceDetector = FaceDetector()
        self.eyeDetector = EyeDetector()
        self.markDetector = MarkDetector(self.faceDetector)

        # Setup process and queues for multiprocessing.
        self.img_queue = Queue()
        self.box_queue = Queue()
        self.img_queue.put(frame)
        self.box_process = Process(target=self.get_face, args=(self.markDetector,))
        self.box_process.start()

        h, w = frame.shape[:2]
        self.poseEstimator = PoseEstimator(img_size=(h, w))

        self.ALARM_ON = False
        self.PREV_ALARM_ON = False

    def get_face(self, detector):
        """Get face from image queue. This function is used for multiprocessing"""
        while True:
            image = self.img_queue.get()
            box = detector.extract_cnn_facebox(image)
            self.box_queue.put(box)

    def alert_driver(self, path = 'alarm.wav'):
        t = Thread( target = playsound.playsound, args = (path,) )
        t.deamon = True
        t.start()

    @staticmethod
    def show_text(frame, roll, pitch, yaw, ear, ALARM_ON):
        """Display the computed Eye Aspect Ratio, Euler angles, and alert message."""

        cv2.putText(frame, "Roll: {}".format(roll), (frame.shape[1]-235, frame.shape[0]-5),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        cv2.putText(frame, "Pitch: {}".format(pitch), (frame.shape[1]-155, frame.shape[0]-5),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        cv2.putText(frame, "Yaw: {}".format(yaw), (frame.shape[1]-75, frame.shape[0]-5),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        cv2.putText(frame, "Eye Aspect Ratio: {:.2f}".format(ear), (5, frame.shape[0]-5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        if ALARM_ON:
            cv2.putText(frame, "ALERT!", (frame.shape[1]-116, 30),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 2)

    def start(self):
        while True:

            # get frame from videofeed and feed frame to img_queue
            frame = self.videofeed.get_frame()
            self.img_queue.put(frame)

            # Get face from box queue.
            facebox = self.box_queue.get()

            if facebox is not None:

                # Detect landmarks from image of 128x128.
                face_img = frame[facebox[1]: facebox[3],
                                facebox[0]: facebox[2]]
                face_img = cv2.resize(face_img, (CNN_INPUT_SIZE, CNN_INPUT_SIZE))
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                marks = self.markDetector.detect_marks(face_img)

                # Convert the marks locations from local CNN to global image.
                marks *= (facebox[2] - facebox[0])
                marks[:, 0] += facebox[0]
                marks[:, 1] += facebox[1]

                # Uncomment following line to show raw marks.
                self.markDetector.draw(frame, marks, color=(0, 255, 0))

                # Try pose estimation with 68 points.
                pose = self.poseEstimator.solve_pose_by_68_points(marks)

                # Uncomment following line to draw pose annotaion on frame.
                self.poseEstimator.draw_annotation_box(
                    frame, pose[0], pose[1], color=(0,255, 0))
 
                # Calculate Eye Aspect Ratio 
                ear = self.eyeDetector.get_eye(frame, facebox)

                # Calculate Euler Angles
                roll, pitch, yaw = self.poseEstimator.get_Euler_Angles(
                    np.array([pose[0][0], pose[0][1], pose[0][2]]),
                    np.array([pose[1][0], pose[1][1], pose[1][2]]))

                # Check if driver is asleep by comparing EAR to EAR threshold 
                # and checking head roll if below roll threshold, and play 
                # alarm if needed

                if ear < self.EYE_AR_THRESH and not self.T1 is None and not self.ALARM_ON:
                    if time.time() - self.T1 > self.TIME_THRESH:
                        self.ALARM_ON = True
                        self.alert_driver()
                        self.T1 = None
                elif ear < self.EYE_AR_THRESH and self.T1 is None:
                    self.T1 = time.time()
                else:
                    self.T1 = None
                    self.ALARM_ON = False

                if abs(roll) > self.ROLL_THRESH and not self.T2 is None and not self.ALARM_ON:
                    if time.time() - self.T2 > self.TIME_THRESH:
                        self.ALARM_ON = True
                        self.alert_driver()
                        self.T2 = None
                elif abs(roll) > self.ROLL_THRESH and self.T2 is None:
                    self.T2 = time.time()
                else:
                    self.T2 = None
                    self.ALARM_ON = False

                self.show_text(frame, roll, pitch, yaw, ear, self.ALARM_ON)

            if self.videofeed.set_frame(frame):
                break

        # Clean up the multiprocessing process.
        self.box_process.terminate()
        self.box_process.join()


if __name__ == '__main__':
    detector = Detector(EYE_AR_THRESH = 0.29, TIME_THRESH = 3)
    detector.start()
