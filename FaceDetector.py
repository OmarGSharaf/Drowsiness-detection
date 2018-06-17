import numpy as np
import cv2

class FaceDetector:
    """Detect human face from image"""

    def __init__(self,
                 dnn_proto_text='assets/deploy.prototxt',
                 dnn_model='assets/res10_300x300_ssd_iter_140000.caffemodel'):

        # load our serialized model from disk
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe(dnn_proto_text, dnn_model)
        self.detection_result = None

    def get_faceboxes(self, frame, threshold=0.5):

        confidences = []
        faceboxes = []

        # grab the frame dimensions and convert it to a blob
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0))
    
        # pass the blob through the network and obtain the detections and
        # predictions
        self.net.setInput(blob)
        detections = self.net.forward()

        for result in detections[0, 0, :, :]:
            
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = result[2]

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
            if confidence > threshold:

                # compute the (x, y)-coordinates of the bounding box for the
                # object
                startX = int(result[3] * w)
                startY = int(result[4] * h)
                endX = int(result[5] * w)
                endY = int(result[6] * h)
                
                confidences.append(confidence)
                faceboxes.append([startX, startY, endX, endY])

        self.detection_result = [faceboxes, confidences]

        return confidences, faceboxes

    def draw(self, image):
        """Draw the detection result on image"""
        
        for facebox, conf in self.detection_result:
            cv2.rectangle(image, (facebox[0], facebox[1]),
                          (facebox[2], facebox[3]), (0, 255, 0))
            label = "face: %.4f" % conf
            label_size, base_line = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            cv2.rectangle(image, (facebox[0], facebox[1] - label_size[1]),
                          (facebox[0] + label_size[0],
                           facebox[1] + base_line),
                          (0, 255, 0), cv2.FILLED)
            cv2.putText(image, label, (facebox[0], facebox[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))