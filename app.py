from flask import Flask,request,jsonify
from netobjects import TCPConnection
import configparser,os
#import tcpserver
from queue import Queue
import base64
app=Flask(__name__)
configs=configparser.ConfigParser()
configs.read("configs.ini")
data={}#{int:Queue}
connections={}
app.route('/')
def main():
    return "main page"
@app.route('/addcontroller',methods=['POST'])
def add_controller():
        details=request.get_json()
    #data.put(request.json.get("b64data"))
    #try:
        if len(connections.keys())>1:
            
            _instance=connections.keys()[0].clone()#prototype
            
            _instance.source_ip=details["source_ip"]
            _instance.destination_ip=details["destination_ip"]
            _instance.source_port=details["source_port"]
            _instance.destination_port=details["destination_port"]
            _instance.action=details["action"]#storeDB|storefile|send
            _instance.enctype=details["enctype"]
        else:
            _instance=TCPConnection(details["source_ip"],details["destination_ip"],details["source_port"],details["destination_port"],details["action"],details["enctype"])
        print(_instance.id)
        connections[int(_instance.id)]=_instance
        return jsonify({"message":"successfully added","id":_instance.id})
    #except KeyError:
    #    return jsonify("not sufficient arguments!"),400      
    #except Exception as ex:
    #    return jsonify(f"Unknown error occured {str(ex)}"),500

@app.route("/get/allconnections")
def get_all_connections():
    return jsonify([x.__json__() for x in connections.values()])
@app.route('/get/<id>')
def get_connection_by_id(id):
    try:
        return jsonify(connections[int(id)].__json__())
    except Exception as ex:
        return jsonify({"message":"Error on getting data","error":str(ex)}),500
@app.route('/save/data/<id>',methods=["POST"])
def add_date(id):
    if int(id) not in data.keys():
        data[int(id)]=Queue()    
    data[int(id)].put(str(request.json.get("b64data")))
    conn=connections.get(int(id))
    
    if conn:
        conn.recieved+=3*(len(request.json.get("b64data").encode())//4)#padding chars not handled
    return jsonify({"message":"successfully added","keys": str(data.keys())})

@app.route('/save/db/<_id>')
def saveinDB(_id):
    from models import DataTable
    iterator=0
    joined_data=''
    while 1:
        if data[int(_id)].empty():
            break
        joined_data+=str(data[int(_id)].get())
        
        iterator+=1
    DataTable.insert(Val=joined_data,TID=_id).execute()
    return jsonify(f"Saved Successfully saved {iterator} chunks")
    
@app.route('/save/file/<filename>/<id>')
def savetofile(filename,id):
    fullpath=configs.get("AppConfig","filespath")+filename
    if os.path.exists(fullpath):
        return jsonify({"message":"duplicate filename"}),400
    iterator=0
    while 1:
        if data[int(id)].empty():
            break
        chunk=data[int(id)].get()
        with open(fullpath,"ab") as f:
            f.write(base64.b64decode(chunk.encode()))
        iterator+=1
    f.close()
    
    return f"{iterator} Chunks written in {filename}"
app.run(debug=True)