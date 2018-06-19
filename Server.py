import socket, threading, cv2, sys, time
from Videofeed import Videofeed
from Detector import Detector
from OpSystemDetector import detectOpSystem

class StopAssignments(Exception): pass

class Server:
    def __init__(self, TCP_IP = "127.0.0.1", TCP_PORT = "8080", BUFFER_SIZE = 32768):
        self.BUFFER_SIZE = BUFFER_SIZE
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((TCP_IP, int(TCP_PORT)))
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.listen(5)
        self.vf = Videofeed("server")
        self.client_socket = None
        self.ALARM_ON = False
        self.PREV_ALARM_ON = False
        print ("\n[INFO] Server IP: %s" %(TCP_IP))
        print ("[INFO] Server is listening on port: %s" %(TCP_PORT))

    def send_alarm_status(self, ALARM_ON):
        if self.PREV_ALARM_ON != self.ALARM_ON:
            self.PREV_ALARM_ON = self.ALARM_ON
            self.client_socket.send( str(self.ALARM_ON).encode('utf-8') )

    def receive_data(self):
        data = b''
        while True:
            part = self.client_socket.recv(self.BUFFER_SIZE)
            data += part
            if len(part) < self.BUFFER_SIZE: break
        if sys.getsizeof(data)<40:
            print ("[INFO] Client stopped sending messages")
            raise StopAssignments
        return data

    def start(self):
        self.client_socket, addr = self.server_socket.accept()
        print ("[INFO] connection received from: %s\n" %(addr[1])),
        
        data = self.receive_data()
        frame = self.vf.convert_to_frame(data)
        self.detector = Detector(frame, EYE_AR_THRESH = 0.24, ROLL_THRESH = 15, TIME_THRESH = 3)
        self.run(self.client_socket)

    def run(self, client_socket):
        while client_socket:
            try:
                data = self.receive_data()
                frame = self.vf.convert_to_frame(data)
                self.ALARM_ON = self.detector.detect_drowsiness(frame)
                self.send_alarm_status(self.ALARM_ON)
                if self.vf.show_frame(frame):
                    break
            except StopAssignments:
                break      
            except socket.error as e:
                print("[ERROR] ", e)
                break
            except Exception as e:
                print("[ERROR] ", e)
                break

        self.terminate()

    def terminate(self):
        self.client_socket.send(b'eof')
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        self.server_socket.close()

if __name__ == "__main__":
    # multiprocessing may not work on Windows and macOS, check OS for safety.
    detectOpSystem()

    server = Server()
    server.start()
