import argparse, time, cv2, glob

class Videofeed:
    
    def __init__(self, name = "test"):
        self.name = name
        self.frame = None

    def start(self):
        for index in glob.glob("/dev/video?"):
            self.vs = cv2.VideoCapture(index)

        time.sleep(1.0)
    
    def get_frame(self):
        _, frame = self.vs.read()
        w = 450
        frame = cv2.resize(frame, (w, int(frame.shape[0] * w / frame.shape[1])), interpolation = cv2.INTER_AREA)
        #h = 680
        #frame = cv2.resize(frame, (int(frame.shape[0] * h / frame.shape[1]), h), interpolation = cv2.INTER_AREA)
        frame = cv2.flip(frame, 2)
        return frame

    def set_frame(self, stream):
        cv2.imshow(self.name, stream)
        key = cv2.waitKey(10)
        if key == 27:
            cv2.destroyAllWindows()
            return True

if __name__ == "__main__" :
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", type=str, default="test", help="name of camera")
    ap.add_argument("-w", "--webcam", type=int, default=0, help="index of webcam on system")
    args = vars(ap.parse_args())
    
    sender = Videofeed("sender")
    receiver = Videofeed("receiver")
    sender.start()
    while True:
        stream = sender.get_frame()
        receiver.set_frame(stream)

