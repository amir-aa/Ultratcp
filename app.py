from flask import Flask,request,jsonify,render_template,send_from_directory,url_for
from netobjects import TCPConnection
import configparser,os
from forwarder import TCPSender
from queue import Queue
import base64,random
from flask_cors import CORS
import requests
app=Flask(__name__)
CORS(app)
configs=configparser.ConfigParser()
configs.read("configs.ini")
forwardto,forwardto_port=configs.get("AppConfig","forwardto").split(":")
tcp_proto=TCPSender(forwardto,int(forwardto_port),Queue())
inputcounter=0
def flush_queue(conn:TCPConnection):
            if conn.action=='db':
                requests.post(url_for('saveinDB', _external=True,_id=conn.id))
                
            elif conn.action=="forward":
                tcp_thread=tcp_proto.clone()
                tcp_thread.dataqueue=data[int(conn.id)]
                tcp_thread.run()
                
            else:#FS or nothing in peers
                from datetime import datetime
                current_datetime=datetime.now()
                if "yes" in str(configs.get("AppConfig","onefile")).lower():
                    formatted_datetime = current_datetime.strftime("%Y_%m_%d")
                    fname=str(formatted_datetime)+"_ID_"+str(conn.id)+".bin"
                else:
                    formatted_datetime = current_datetime.strftime("%Y_%m_%d_%H_%M_%S")
                    fname=str(formatted_datetime)+".bin"
                conn.flush_data(fname,data[int(conn.id)])
            conn.recieved=0
def increment_inputCounter(number:int):
    global inputcounter
    inputcounter+=number
def flush_inputcounter():
    global inputcounter
    inputcounter=0
data={}#{int:Queue}
connections={}
@app.route('/')
def main():
    return render_template('i.html',apiaddr=configs.get("AppConfig","appaddress"),maxknob=configs.get("AppConfig","queuelen"))
def generate_chart_data():
    labels = ['January', 'February', 'March', 'April', 'May']
    data = [random.randint(10, 100) for _ in range(len(labels))]
    return {'labels': labels, 'data': data}

@app.route('/chart-data')
def chart_data():
    return jsonify(generate_chart_data())


def generate_knob_data():
    result={'value1': len(connections.keys()), 'value2': inputcounter}
    flush_inputcounter()
    return result

@app.route('/knob-data')
def knob_data():
    return jsonify(generate_knob_data())

@app.route('/addcontroller',methods=['POST'])
def add_controller():
        details=request.get_json()
    #data.put(request.json.get("b64data"))
    #try:
        if len(connections.keys())>1:
            try:
                _instance=connections.keys()[0].clone()#prototype
            except TypeError:
                _instance=TCPConnection(details["source_ip"],details["destination_ip"],details["source_port"],details["destination_port"],details["action"],details["enctype"])
            except Exception as ex:
                print("unknown error ",str(ex))
            
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
        datalen=3*(len(request.json.get("b64data").encode())//4)#padding chars not handled
        conn.recieved+=datalen
        increment_inputCounter(datalen)
        if conn.recieved> int(configs.get("AppConfig","queuelen")) :
            #more than capacity | write and saving data is required
            flush_queue(conn)
            
            return jsonify({"message":"successfully added But Queue has flushed due to full capacity.","keys": str(data.keys())}),201
    return jsonify({"message":"successfully added","keys": str(data.keys())}),200

@app.route('/save/db/<_id>',methods=['POST'])
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

@app.route('/remove/conn/<id>',methods=["POST"])
def removeConnection(id):
    if int(id)==0:
        connections.clear()
        return "successfully cleared connection"
    #first saving data !
    conn=connections.get(int(id))
    flush_queue(conn)
    del connections[int(id)]
    return f"successfully deleted connection {id}"

"""
@app.route('/static/vendors/bower_components/<path>')
def routi(path):
    return send_from_directory('static/vendors/browser_components/', path)"""
app.run(debug=True)