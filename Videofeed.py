import argparse, imutils, time, cv2, sys, numpy, io, glob
from imutils.video import VideoStream
from PIL import Image

class Videofeed:
    
    def __init__(self, name = "test"):
        self.name = name
        self.frame = None

    def start(self):
        for index in glob.glob("/dev/video?"):
            self.vs = VideoStream(index)
            self.vs.start()

        time.sleep(1.0)

    def stop(self):
        self.vs.stop()
        cv2.destroyAllWindows()

    def get_frame(self):
        self.frame = imutils.resize(self.vs.read(), width= 480)
        b = io.BytesIO()
        Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)).save(b, 'jpeg')
        return b.getvalue()

    def set_frame(self, stream):
        self.frame = self.convert_to_frame(stream)
        self.show_frame(self.frame)

    def convert_to_frame(self, stream):
        self.frame = Image.open(io.BytesIO(stream))
        self.frame = cv2.cvtColor(numpy.array(self.frame, dtype=numpy.uint8), cv2.COLOR_RGB2BGR)
        self.frame = cv2.flip(self.frame, 2)
        return self.frame

    def show_frame(self, frame):
        cv2.imshow(self.name, frame)
        key = cv2.waitKey(10)
        if key == 27:
            cv2.destroyAllWindows()
            return True   

if __name__ == "__main__" :
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", type=str, default="test", help="name of camera")
    ap.add_argument("-w", "--webcam", type=int, default=0, help="index of webcam on system")
    args = vars(ap.parse_args())
    
    client = Videofeed("client")
    server = Videofeed("server")
    client.start()
    while True:
        stream = client.get_frame()
        server.set_frame(stream)

