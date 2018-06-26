import socket, argparse, signal, time, sys
from ipaddress import ip_address
from playsound import playsound
from threading import Thread
from Videofeed import Videofeed

class Client:
    def __init__(self, path, TCP_IP = "127.0.0.1", TCP_PORT = 8080, BUFFER_SIZE = 32768):
        self.BUFFER_SIZE = BUFFER_SIZE
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(10)
        self.client_socket.connect((str(TCP_IP), TCP_PORT))
        self.client_socket.settimeout(None)
        print ("[INFO] Client connected to server [", TCP_IP, "] on port: ", TCP_PORT)
        self.vf = Videofeed("client")
        self.vf.start()
        self.path = path
        self.ALARM_ON = False

    def str2bool(self, v):
        return v.lower() in ("yes", "true", "t", "1")

    def stop(self):
        self.ALARM_ON = False
        self.vf.stop()
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        sys.exit(1)

    def sound_alarm(self, path):
        while self.ALARM_ON:
            playsound(path)

    def send_frame(self):
        while self.client_socket:
            try:
                data = self.vf.get_frame() 
                self.client_socket.send(data)
            except Exception as e:
                print(e)
                break

    def update_alarm(self):
        while self.client_socket:
            try:
                data = self.client_socket.recv(128).decode("utf-8")
                
                if data.lower() == 'eof': self.stop(); break

                self.ALARM_ON = self.str2bool(data)
                t = Thread( target = self.sound_alarm, args = (self.path,) )
                t.deamon = True
                t.start()
            except Exception as e:
                print(e)
                break

    def start(self):
        t1 = Thread(target=self.send_frame)
        t2 = Thread(target=self.update_alarm)
        t1.deamon = True
        t1.start()
        t2.deamon = True
        t2.start()

        try:
            signal.pause()
        except KeyboardInterrupt:
            self.stop()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--alarm", type = str, default="alarm.wav",
        help="path alarm .WAV file")
    ap.add_argument("-ip", "--IP", type = ip_address, default="127.0.0.1",
        help="host name")
    ap.add_argument("-p", "--port", type = int, default = 8080,
        help="port number")
    args = vars(ap.parse_args())

    while True:
        try:
            print("[INFO] Connecting...")
            client = Client(path = args["alarm"], TCP_IP = args["IP"], TCP_PORT = args["port"])
            client.start()
        except KeyboardInterrupt: 
            break 
        except Exception as e:
            print("[EXCEPTION] ", e, "\n[INFO] Failed to connect to server!\n")
            try: time.sleep(10) 
            except KeyboardInterrupt: break 
            continue