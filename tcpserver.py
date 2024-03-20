import socket,requests,logging
import select,base64,json
connections={}
# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the address and port
server_address = ('', 12345)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(5)
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
            data = sock.recv(1024)
            if data:
                # Process received dataf
                b64data=base64.b64encode(data)
                if client_address in connections.keys():
                    _id=connections[client_address]
                else:
                    resp=requests.post("http://127.0.0.1:5000/addcontroller",json={"source_ip":client_address[0],"source_port":client_address[1]
                                                                     ,"destination_port":12345,"destination_ip":'127.0.0.1',"action":"file","enctype":""})
                    #print(resp.text)
                    #print(dict(json.loads(resp.text))["id"])
                    _id=dict(json.loads(resp.text))["id"]
                    connections[client_address]=_id
                requests.post("http://127.0.0.1:5000/save/data/"+str(_id),json={"b64data":b64data.decode()})

                outputs[sock] = data
            else:
                # Client closed the connection
                print("Client disconnected:", sock.getpeername())
                try:
                    requests.post(f"http://127.0.0.1:5000/remove/conn/{str(connections[client_address])}")
                    del connections[client_address]
                except KeyError:
                    logging.warning(f"Key:{client_address} is not available ")
                print(connections)
                if len(connections.items())<1:
                    requests.post("http://127.0.0.1:5000/remove/conn/0") #handle orphened connections
                
                if sock in outputs:
                    del outputs[sock]
                del inputs[sock]
                sock.close()

    # Handle writable sockets (send outgoing data)
    for sock in writable:
        data = outputs.pop(sock)
        sock.sendall(data)

    # Handle exceptional conditions (errors)
    for sock in exceptional:
        print("Exceptional condition on:", sock.getpeername())
        del inputs[sock]
        if sock in outputs:
            del outputs[sock]
        sock.close()
