import socket, threading
from ClientThread import ClientThread

class Server:
    def __init__(self, TCP_IP = "127.0.0.1", TCP_PORT = "8080",THREAD_INDEX=1, BUFFER_SIZE = 32768):
        self.THREAD_INDEX = THREAD_INDEX
        self.BUFFER_SIZE = BUFFER_SIZE
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((TCP_IP, int(TCP_PORT)))
        self.server_socket.listen(5)
        print "\n[INFO] Server IP: %s" %(TCP_IP)
        print "[INFO] Server is listening on port: %s" %(TCP_PORT)

    def start(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            clientThread = ClientThread(client_socket, addr, self.THREAD_INDEX)
            clientThread.start()
            print "[INFO] THREAD[%s] is created\n" % (self.THREAD_INDEX),
            self.THREAD_INDEX += 1

if __name__ == "__main__":
    server = Server()
    server.start()
        
	
