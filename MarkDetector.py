import numpy as np
import tensorflow as tf

import cv2

class MarkDetector:
    """Facial landmark detector by Convolutional Neural Network"""

    def __init__(self, faceDetector, mark_model='assets/frozen_inference_graph.pb'):
        """Initialization"""

        # A face detector is required for mark detection.
        self.faceDetector = faceDetector

        self.cnn_input_size = 128
        self.marks = None

        # Get a TensorFlow session ready to do landmark detection
        # Load a (frozen) Tensorflow model into memory.
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(mark_model, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        self.graph = detection_graph
        self.sess = tf.Session(graph=detection_graph)

    @staticmethod
    def draw_box(image, boxes, box_color=(255, 255, 255)):
        """Draw square boxes on image"""

        for box in boxes:
            cv2.rectangle(image,
                          (box[0], box[1]),
                          (box[2], box[3]), box_color)

    @staticmethod
    def move_box(box, offset):
        """Move the box to direction specified by vector offset"""

        startX = box[0] + offset[0]
        startY = box[1] + offset[1]
        endX = box[2] + offset[0]
        endY = box[3] + offset[1]
        return [startX, startY, endX, endY]

    @staticmethod
    def get_square_box(box):
        """Get a square box out of the given box, by expanding it."""
		
        startX = box[0]
        startY = box[1]
        endX = box[2]
        endY = box[3]

        box_width = endX - startX
        box_height = endY - startY

        # Check if box is already a square. If not, make it a square.
        diff = box_height - box_width
        delta = int(abs(diff) / 2)

        if diff == 0:                   # Already a square.
            return box
        elif diff > 0:                  # Height > width, a slim box.
            startX -= delta
            endX += delta
            if diff % 2 == 1:
                endX += 1
        else:                           # Width > height, a short box.
            startY -= delta
            endY += delta
            if diff % 2 == 1:
                endY += 1

        # Make sure box is always square.
        assert ((endX - startX) == (endY - startY)), 'Box is not square.'

        return [startX, startY, endX, endY]

    @staticmethod
    def box_in_image(box, image):
        """Check if the box is in image"""

        h = image.shape[0]
        w = image.shape[1]
        return box[0] >= 0 and box[1] >= 0 and box[2] <= w and box[3] <= h

    def extract_cnn_facebox(self, image):
        """Extract face area from image."""

        _, raw_boxes = self.faceDetector.get_faceboxes(frame=image, threshold=0.9)

        for box in raw_boxes:
            # Move box down.
            diff_height_width = (box[3] - box[1]) - (box[2] - box[0])
            offset_y = int(abs(diff_height_width / 2))
            box_moved = self.move_box(box, [0, offset_y])

            # Make box square.
            facebox = self.get_square_box(box_moved)

            if self.box_in_image(facebox, image):
                return facebox

        return None

    def detect_marks(self, image_np):
        """Detect marks from image"""

        # Get result tensor by its name.
        logits_tensor = self.graph.get_tensor_by_name('logits/BiasAdd:0')

        # Actual detection.
        predictions = self.sess.run(
            logits_tensor,
            feed_dict={'input_image_tensor:0': image_np})

        # Convert predictions to landmarks.
        marks = np.array(predictions).flatten()
        marks = np.reshape(marks, (-1, 2))

        return marks

    @staticmethod
    def draw(image, marks, color=(255, 255, 255)):
        """Draw mark points on image"""

        for i, mark in enumerate(marks):
            if i < 37 or i > 48:
                cv2.circle(image, (int(mark[0]), int(
                    mark[1])), 1, color, -1, cv2.LINE_AA)
