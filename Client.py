import socket, playsound, argparse
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
        print "[INFO] Client connected to server[", TCP_IP, "] on port: ", TCP_PORT

    def str2bool(self, v):
        return v.lower() in ("yes", "true", "t", "1")

    def send_frame(self):
        while True:
            data = self.vf.get_frame() 
            self.client_socket.send(data)

    def update_alarm(self):
        while True:
            self.ALARM_ON = self.str2bool( self.client_socket.recv(64))
            self.sound_alarm(self.path)

    def connect(self):
        try:
            t1 = Thread(target=self.send_frame)
            t2 = Thread(target=self.update_alarm)
            t1.deamon = True
            t2.deamon = True
            t1.start()
            t2.start()
        except Exception, e:
            print e
            self.client_socket.close() 
    
    def sound_alarm(self, path):
    	playsound.playsound(path)

if __name__ == "__main__":
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--alarm", type=str, default="alarm.wav",
        help="path alarm .WAV file")
    args = vars(ap.parse_args())

    client = Client(path = args["alarm"])
    client.connect()
	
