# -*- coding: utf-8 -*-
"""
Using Kalman Filter as a point stabilizer to stabiliz a 2D point.

mp = [measuredX, measuredY, xVelocity, yVelocity]       <- measurement vector

Prediction Step:
x = (A * x) + (B * c)
P = (A * P * Aᵀ) + Q     <- Aᵀ is the matrix transpose of A


Correction Step:
S = (H * P * Hᵀ) + R     <- Hᵀ is the matrix transpose of H
K = P * Hᵀ * S⁻¹         <- S⁻¹ is the matrix inverse of S
y = m - (H * x)
x = x + (K * y)
P = (I - (K * H)) * P    <- I is the Identity matrix

If prediction is enabled, the prediction step is looped for n more frames after the above code is executed:

predX = x
predX = (A * predX) + (B * c)


The estimated position of the cursor is in the x vector:

x ← [xPos, yPos, xVel, yVel]

Kalman Filter main parameters
-----------------------------
(A) State transition matrix -> influences the measurement vector.
(B) Control matrix -> influences the control vector (unused). 
(H) Measurement matrix -> influences the Kalman Gain
(Q) Process noise covariance matrix -> implies the process noise covariance.
(R) Measurement noise covariance matrix -> implies the measurement error covariance, 
                                            based on the amount of sensor noise.

"""
import numpy as np

import cv2

class Stabilizer:
    """Using Kalman filter as a point stabilizer."""

    def __init__(self, state_num=4, measure_num=2, cov_process=0.0001, cov_measure=0.05):
        
        # Currently we only support scalar and point, so check user input first.
        assert state_num == 4 or state_num == 2, "Only scalar and point supported, Check state_num please."

        self.state_num = state_num
        self.measure_num = measure_num

        self.filter = cv2.KalmanFilter(state_num, measure_num, 0)   # The filter itself.
        self.state = np.zeros((state_num, 1), dtype=np.float32)     # Store the state.
        self.measurement = np.array((measure_num, 1), np.float32)   # Store the measurement result.
        self.prediction = np.zeros((state_num, 1), np.float32)      # Store the prediction.

        if self.measure_num == 1:   # Kalman parameters setup for scalar.
            self.filter.transitionMatrix = np.array([[1, 1],
                                                     [0, 1]], np.float32)

            self.filter.measurementMatrix = np.array([[1, 1]], np.float32)

            self.filter.processNoiseCov = np.array([[1, 0],
                                                    [0, 1]], np.float32) * cov_process

            self.filter.measurementNoiseCov = np.array([[1]], np.float32) * cov_measure

        
        if self.measure_num == 2:   # Kalman parameters setup for point.
            self.filter.transitionMatrix = np.array([[1, 0, 1, 0],
                                                     [0, 1, 0, 1],
                                                     [0, 0, 1, 0],
                                                     [0, 0, 0, 1]], np.float32)

            self.filter.measurementMatrix = np.array([[1, 0, 0, 0],
                                                      [0, 1, 0, 0]], np.float32)

            self.filter.processNoiseCov = np.array([[1, 0, 0, 0],
                                                    [0, 1, 0, 0],
                                                    [0, 0, 1, 0],
                                                    [0, 0, 0, 1]], np.float32) * cov_process

            self.filter.measurementNoiseCov = np.array([[1, 0],
                                                        [0, 1]], np.float32) * cov_measure

    def update(self, measurement):
        """Update the filter"""
        # Make kalman prediction
        self.prediction = self.filter.predict()

        # Get new measurement
        if self.measure_num == 1:
            self.measurement = np.array([[np.float32(measurement[0])]])
        else:
            self.measurement = np.array([[np.float32(measurement[0])],
                                         [np.float32(measurement[1])]])

        # Correct according to mesurement
        self.filter.correct(self.measurement)

        # Update state value.
        self.state = self.filter.statePost

    def set_q_r(self, cov_process=0.1, cov_measure=0.001):
        """Set new value for processNoiseCov and measurementNoiseCov."""
        if self.measure_num == 1:
            self.filter.processNoiseCov = np.array([[1, 0],
                                                    [0, 1]], np.float32) * cov_process
            self.filter.measurementNoiseCov = np.array(
                [[1]], np.float32) * cov_measure
        else:
            self.filter.processNoiseCov = np.array([[1, 0, 0, 0],
                                                    [0, 1, 0, 0],
                                                    [0, 0, 1, 0],
                                                    [0, 0, 0, 1]], np.float32) * cov_process
            self.filter.measurementNoiseCov = np.array([[1, 0],
                                                        [0, 1]], np.float32) * cov_measure


def main():
    """Test code"""
    global mp
    mp = np.array((2, 1), np.float32)  # measurement
    
    def onmouse(k, x, y, s, p):
        global mp
        mp = np.array([[np.float32(x)], [np.float32(y)]])

    cv2.namedWindow("kalman")
    cv2.setMouseCallback("kalman", onmouse)
    kalman = Stabilizer(4, 2)
    frame = np.zeros((480, 640, 3), np.uint8)  # drawing canvas

    while True:
        kalman.update(mp)
        point = kalman.prediction
        state = kalman.filter.statePost
        cv2.circle(frame, (state[0], state[1]), 2, (255, 0, 0), -1) # Blue
        cv2.circle(frame, (point[0], point[1]), 2, (0, 255, 0), -1) # Green
        cv2.imshow("kalman", frame)
        k = cv2.waitKey(30) & 0xFF
        if k == 27:
            break


if __name__ == '__main__':
    main()
