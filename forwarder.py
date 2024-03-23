import threading,logging
import socket,base64
import copy
from queue import Queue
class TCPSender(threading.Thread):
    def __init__(self, host:str, port:int, data:Queue):
        super().__init__()
        self.host = host
        self.port = port
        self.dataqueue = data
    
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))
                while not self.dataqueue.empty():
                    sock.sendall(base64.b64decode(self.dataqueue.get()))
                print(f"Data sent to {self.host}:{self.port}")
        except Exception as e:
            print(f"Error occurred while sending data:{str(e)}")
            logging.error(f"Error occurred while sending data:{str(e)}")

    def clone(self):
        return copy.copy(self)
