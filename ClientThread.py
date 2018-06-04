import socket, threading, sys
from Videofeed import Videofeed
from cv2 import destroyAllWindows
from Detector import Detector
from Detector import StopAssignments

threadLimiter = threading.BoundedSemaphore(5)

class ClientThread(threading.Thread):
    

    def __init__(self, client_socket, addr, THREAD_INDEX ,BUFFER_SIZE = 65536):
        self.THREAD_INDEX = THREAD_INDEX
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.addr = addr
        self.BUFFER_SIZE = BUFFER_SIZE
        self.detector = Detector()
        self.vf = Videofeed(str(self.THREAD_INDEX))
        self.ALARM_ON = False
        self.PREV_ALARM_ON = False
        self.frame = None
        print "[INFO] connection received from: %s\n" %(self.addr[1]),

    def send_alarm_status(self, ALARM_ON):
        if self.PREV_ALARM_ON <> self.ALARM_ON:
            self.PREV_ALARM_ON = self.ALARM_ON
            self.client_socket.send( str(self.ALARM_ON) )

    def receive_data(self):
        data = b''
        while True:
            part = self.client_socket.recv(self.BUFFER_SIZE)
            data += part
            if len(part) < self.BUFFER_SIZE: break
        if sys.getsizeof(data)<40:
            print "[INFO] Client stopped sending messages"
            raise StopAssignments
        return data     

    def run(self):
            threadLimiter.acquire()
            while self.client_socket:
                try:
                    print "1"
                    data = self.receive_data()
                    print "2"
                    self.frame = self.vf.convert_to_frame(data)
                    print "3"
                    self.ALARM_ON = self.detector.detect_drowsiness(self.frame)
                    print "4"
                    self.send_alarm_status(self.ALARM_ON)
                    print "5\n"
                except StopAssignments:
                    destroyAllWindows()
                    break                
                except socket.error, e:
                    destroyAllWindows() 
                    print e
                    break
                except Exception,e:
                    print e
                    break

            self.client_socket.close()
            threadLimiter.release()
            print "[INFO] Socket closed on port: %s\n" %(self.addr[1]),
            print "[INFO] Thread %s is released\n" %(self.THREAD_INDEX),
