import socket, playsound, argparse, signal
from threading import Thread
from Videofeed import Videofeed

class Client:
    def __init__(self, path, TCP_IP = "127.0.0.1", TCP_PORT = "8080", BUFFER_SIZE = 32768):
        self.BUFFER_SIZE = BUFFER_SIZE
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((TCP_IP, int(TCP_PORT)))
        self.vf = Videofeed("client", 0)
        self.vf.start()
        self.path = path
        self.ALARM_ON = False
        self.EXIT = False
        print "[INFO] Client connected to server[", TCP_IP, "] on port: ", TCP_PORT

    def str2bool(self, v):
        return v.lower() in ("yes", "true", "t", "1")

    def clean(self, e):
        try:
            self.EXIT = True
            self.ALARM_ON = False
            self.vf.stop()
            self.client_socket.shutdown(2)
            self.client_socket.close()
            print e
        except socket.error, e:
            print e

    def sound_alarm(self, path):
        while self.ALARM_ON:
            playsound.playsound(path)

    def send_frame(self):
        while not self.EXIT:
            try:
                data = self.vf.get_frame() 
                self.client_socket.send(data)
            except socket.error, e:
                self.clean(e)
                break
            except Exception, e:
                self.clean(e)
                break

    def update_alarm(self):
        while not self.EXIT:
            try:
                self.ALARM_ON = self.str2bool( self.client_socket.recv(64) )
                t = Thread( target = self.sound_alarm, args = (self.path,) )
                t.deamon = True
                t.start()
            except socket.error, e:
                self.clean(e)
                break
            except Exception, e:
                self.clean(e)
                break

    def connect(self):
        t1 = Thread(target=self.send_frame)
        t2 = Thread(target=self.update_alarm)
        t1.deamon = True
        t2.deamon = True
        t1.start()
        t2.start()

        try:
            signal.pause()
        except KeyboardInterrupt, e:
            print "\nKeyboardInterrupt"
            self.clean(e)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--alarm", type=str, default="alarm.wav",
        help="path alarm .WAV file")
    args = vars(ap.parse_args())

    client = Client(path = args["alarm"])
    client.connect()
