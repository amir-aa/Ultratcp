import copy,json,secrets
from queue import Queue
from models import tbl_TCPConnection
class TCPConnection:
    def __init__(self,source_ip,destination_ip,source_port,destination_port,action,enctype=None):
        
        self.source_ip=source_ip
        self.destination_ip=destination_ip
        self.source_port=source_port
        self.destination_port=destination_port
        self.action=action#DB|file|forward
        self.enctype=enctype
        self.recieved=0
        
        db_object=tbl_TCPConnection.insert(source_ip=source_ip,destination_ip=destination_ip,source_port=source_port,destination_port=destination_port,action=action,enctype=enctype).execute()
        self.id=db_object
    def clone(self):
        return copy.copy(self)

    def __str__(self):
        return f"Source IP: {self.source_ip}, Destination IP: {self.destination_ip}, " \
               f"Source Port: {self.source_port}, Destination Port: {self.destination_port}"
    def __json__(self):
        return {
            "ID":self.id,
            "source_ip":self.source_ip,
            "destination_ip":self.destination_ip,
            "source_port":self.source_port,
            "destination_port":self.destination_port,
            "enctype":self.enctype,
            "action":self.action,
            "dl":self.recieved
           
        }
    def flush_data(self,filename:str,queue:Queue):
        import base64
        """flush function saves all data in file and turns dl value(counter) to 0 bytes"""
        with open(filename,'ab') as f:
            for i in range(queue.qsize()):
                f.write(base64.b64decode(str(queue.get()).encode()))
            f.close()
        
            
#t1=TCPConnection("2","2",1,3,"forward","No")
#t2=TCPConnection("22","2",1,3,"forward","No")
#t3=t2.clone()
#print(t1.id)
#print(t2.id)
#t3.enctype="AES"
#print(t3.id)