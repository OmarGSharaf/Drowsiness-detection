import argparse, imutils, time, cv2, sys, numpy, io 
from imutils.video import VideoStream
from PIL import Image

class Videofeed:
    
    def __init__(self, name = "test", index = 0):
        self.index = index
        self.name = name
        self.frame = None
        self.vs = None

    def start(self):
        self.vs = VideoStream(self.index).start()
        time.sleep(1.0)

    def clean(self):
        self.vs.stop()
        cv2.destroyAllWindows()

    def check_camera_index(self):
        key = cv2.waitKey(1)
        if key == ord("n"): 
            self.index += 1 
            self.vs = VideoStream(self.index).start()
            if not self.vs: 
                self.index = 0
                self.vs = VideoStream(self.index).start()
    
    def get_frame(self):
        self.frame = imutils.resize(self.vs.read(), width=450)
        self.check_camera_index()
        b = io.BytesIO()
        Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)).save(b, 'jpeg')
        return b.getvalue()


    def set_frame(self, stream):
        self.frame = Image.open(io.BytesIO(stream))
        self.frame = cv2.cvtColor(numpy.array(self.frame), cv2.COLOR_RGB2BGR)
        cv2.imshow(self.name, self.frame)
        cv2.waitKey(1)

    def convert_to_frame(self, stream):
        self.frame = Image.open(io.BytesIO(stream))
        self.frame = cv2.cvtColor(numpy.array(self.frame), cv2.COLOR_RGB2BGR)
        return self.frame

if __name__ == "__main__" :
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", type=str, default="test", help="name of camera")
    ap.add_argument("-w", "--webcam", type=int, default=0, help="index of webcam on system")
    args = vars(ap.parse_args())
    
    client = Videofeed("client", 0)
    server = Videofeed("server", 0)
    client.start()
    while True:
        stream = client.get_frame()
        server.set_frame(stream)

