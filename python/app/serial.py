import json
from flask import Blueprint
from serial.tools import list_ports

# Blueprintのオブジェクトを生成する
app = Blueprint('serial', __name__)

# Serial port REST-API
@app.route("/ports", methods=['GET'])
def get_ports():
    ports = [port.name for port in list_ports.comports()]
    return json.dumps(ports, indent=2)

@app.route("/ports/<string:port>", methods=['GET'])
def get_port(port):
    selected_ports = [com_port for com_port in list_ports.comports() if com_port.name.lower() == port.lower()]
    ret_obj = {
        "device":None,
        "name": None,
        "description": None,
        "hwid": None,
        "vid": None,
        "pid": None,
        "serial_number": None,
        "location": None,
        "manufacturer": None,
        "product": None,
        "interface": None
    }
    if 1 == len(selected_ports):
        ret_obj = vars(selected_ports[0])
    return json.dumps(ret_obj, indent=2)
