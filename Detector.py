import cv2, time, numpy as np
from multiprocessing import Process, Queue
from FaceDetector import FaceDetector
from EyeDetector import EyeDetector
from MarkDetector import MarkDetector
from PoseEstimator import PoseEstimator
from stabilizer import Stabilizer

CNN_INPUT_SIZE = 128

class Detector:
    def __init__(self, frame, EYE_AR_THRESH = 0.3, ROLL_THRESH = 20, TIME_THRESH = 10):
        
        self.EYE_AR_THRESH = EYE_AR_THRESH
        self.ROLL_THRESH = ROLL_THRESH
        self.TIME_THRESH = TIME_THRESH
        self.ALARM_ON = False
        self.T = None

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
        self.pose_stabilizers = [Stabilizer(state_num=2,
                                            measure_num=1,
                                            cov_process=0.1,
                                            cov_measure=0.1) for _ in range(6)]

    def get_face(self, detector):
        """Get face from image queue. This function is used for multiprocessing"""
        while True:
            image = self.img_queue.get()
            box = detector.extract_cnn_facebox(image)
            self.box_queue.put(box)

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

    def detect_drowsiness(self, frame):
        # get frame from Server and feed frame to img_queue
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
            unstable_pose = self.poseEstimator.solve_pose_by_68_points(marks)

            # Stabilize the pose.
            pose = []
            pose_np = np.array(unstable_pose).flatten()
            for value, ps_stb in zip(pose_np, self.pose_stabilizers):
                ps_stb.update([value])
                pose.append(ps_stb.state[0])
            pose = np.reshape(pose, (-1, 3))

            # Uncomment following line to draw stabile pose annotaion on frame.
            self.poseEstimator.draw_annotation_box(
                frame, pose[0], pose[1], color=(0,255, 0))

            # Calculate Eye Aspect Ratio 
            ear = self.eyeDetector.get_eye(frame, facebox)

            # Calculate Euler Angles
            roll, pitch, yaw = self.poseEstimator.get_Euler_Angles(
                np.array([[pose[0][0]], [pose[0][1]], [pose[0][2]]]),
                np.array([[pose[1][0]], [pose[1][1]], [pose[1][2]]]))

            if ear < self.EYE_AR_THRESH or abs(roll) > self.ROLL_THRESH:
                if self.T is None:
                    self.T = time.time()
                elif time.time() - self.T > self.TIME_THRESH:
                    self.ALARM_ON = True
            else:
                self.T = None
                self.ALARM_ON = False      

            self.show_text(frame, roll, pitch, yaw, ear, self.ALARM_ON)

        return self.ALARM_ON

        # Clean up the multiprocessing process.
        self.box_process.terminate()
        self.box_process.join()

