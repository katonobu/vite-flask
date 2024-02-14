import json
import serial
from flask import Blueprint
from serial.tools import list_ports

serial_objs = {}

# Blueprintのオブジェクトを生成する
app = Blueprint('serial', __name__)

def extract_serial_obj(ser_obj:serial.Serial):
    ret_obj = {
        "name":ser_obj.name,
        "is_open":ser_obj.is_open,
        "baudrate":ser_obj.baudrate,
        "bytesize":ser_obj.bytesize,
        "parity":ser_obj.parity,
        "stopbits":ser_obj.stopbits,
        "timeout":ser_obj.timeout,
        "write_timeout":ser_obj.write_timeout,
        "inter_byte_timeout":ser_obj.inter_byte_timeout,
        "xonxoff":ser_obj.xonxoff,
        "rtscts":ser_obj.rtscts,
        "dsrdtr":ser_obj.dsrdtr,
        "rts":ser_obj.rts,
        "dtr":ser_obj.dtr
    }
    if ser_obj.is_open:
        ret_obj.update({
            "cts":ser_obj.cts,
            "dts":ser_obj.dsr,
            "ri":ser_obj.ri,
            "cd":ser_obj.cd
        })
    return ret_obj

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

@app.route("/ports/<string:port>/status", methods=['GET'])
def get_port_status(port):
    ret_obj = {port:None}
    selected_ports = [com_port for com_port in list_ports.comports() if com_port.name.lower() == port.lower()]
    if 1 == len(selected_ports):
        target_port = selected_ports[0].name
        target_obj = serial_objs.get(target_port)
        if target_obj:
            ret_obj.update({port:extract_serial_obj(target_obj)})
    return ret_obj

