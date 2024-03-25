import socket,requests,logging
import select,base64,json
import configparser

conf=configparser.ConfigParser()
conf.read("configs.ini")
def getAction_by_addr(addr:str):
    with open('peers.conf','r') as f:
        lines=f.readlines()
        for line in lines:
            if addr in line:
                if "FS" in line:
                    return 'file'
                elif "DB" in line:
                    return 'db'
                else:
                    return 'forward'
        f.close()
    return None
            
connections={}
# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the address and port
server_address = (conf.get("AppConfig","bindaddress"), int(conf.get("AppConfig","port")))
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(int(conf.get("AppConfig","port")))
server_socket.setblocking(False)

# Create dictionaries to track sockets and their data
inputs = {server_socket: server_socket}
outputs = {}

while inputs:
    # Use select to wait for events on sockets
    readable, writable, exceptional = select.select(inputs.keys(), outputs.keys(), inputs.keys())

    # Handle readable sockets (new connections or incoming data)
    for sock in readable:
        if sock is server_socket:
            # Accept new connections
            client_socket, client_address = sock.accept()
            print("Connection from:", client_address)
            client_socket.setblocking(False)
            inputs[client_socket] = client_socket
        else:
            # Handle data from an existing client socket
            data = sock.recv(int(conf.get("AppConfig","buffer")))
            if data:
                #New connection handling------------------------------------------
                b64data=base64.b64encode(data)
                if client_address in connections.keys():
                    _id=connections[client_address]
                else:#no duplicate
                    action=getAction_by_addr(client_address[0])
                    #print(action)
                    if not action:
                        action='file'
                    resp=requests.post(conf.get("AppConfig","appaddress")+"/addcontroller",json={"source_ip":client_address[0],"source_port":client_address[1]
                                                                     ,"destination_port":conf.get("AppConfig","port"),"destination_ip":conf.get("AppConfig","bindaddress"),"action":action,"enctype":""})
                    
                   
                    _id=dict(json.loads(resp.text))["id"]
                    sock.send(str(_id).encode())
                    connections[client_address]=_id
                    #END OF New connection handling-------------------------------
                    # Process received data
                requests.post(conf.get("AppConfig","appaddress")+"/save/data/"+str(_id),json={"b64data":b64data.decode()})

                outputs[sock] = data
            else:
                # Client closed the connection
                print("Client disconnected:", sock.getpeername())
                try:
                    requests.post(f'{conf.get("AppConfig","appaddress")}/remove/conn/{str(connections[client_address])}')
                    del connections[client_address]
                except KeyError:
                    logging.warning(f"Key:{client_address} is not available ")
                print(connections)
                if len(connections.items())<1:
                    requests.post(conf.get("AppConfig","appaddress")+"/remove/conn/0") #handle orphened connections
                
                if sock in outputs:
                    del outputs[sock]
                del inputs[sock]
                sock.close()
    # Handle writable sockets (send outgoing data)
    for sock in writable:
        data = outputs.pop(sock)
        sock.sendall(data)

    #Handle Exceptions
    for sock in exceptional:
        print("Exceptional condition on:", sock.getpeername())
        del inputs[sock]
        if sock in outputs:
            del outputs[sock]
        sock.close()()
