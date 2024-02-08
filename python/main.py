# このドキュメントをベースに進化させる。
# Flask-SocketIO
#  https://flask-socketio.readthedocs.io/en/latest/index.html

import time
import sys
import os
import mimetypes
import json
import webbrowser
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from engineio.async_drivers import threading # to avoid runtime error in .exe
from serial.tools import list_ports

static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "js","dist"))
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # pyinstaller option --add-data "..\js\dist:dist" is assumed.
    static_folder = os.path.abspath(os.path.join(sys._MEIPASS,"dist"))

app = Flask(
    __name__,
    static_folder=static_folder, # static_folder is js/dist or dist
    static_url_path=""           # assing url "/" to static folder
)

# MIME type of "text/plain" 対応。
mimetypes.add_type("application/javascript", ".js")

socket = SocketIO(
    app,
#    cors_allowed_origins="*",
    async_mode="threading"  # to avoid runtime error in .exe
)

@socket.on("ping")  # callback if ping event is arrived
def ping(data):
    print(data)
    print(time.time())
    emit("pong", str(time.time()))
 
# static setting for Vite
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/assets/<path:path>")
def send_js(path):
    return send_from_directory(app.static_folder, "assets/"+path)

# Serial port REST-API
@app.route("/ports", methods=['GET'])
def get_ports():
    ports = [port.device for port in list_ports.comports()]
    return json.dumps(ports, indent=2)

@app.route("/ports/<string:port>", methods=['GET'])
def get_port(port):
    selected_ports = [com_port for com_port in list_ports.comports() if com_port.device.lower() == port.lower()]
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

if __name__ =="__main__":
    protocol = "http"
    url = "localhost"
    port = 5001
    try:
        webbrowser.open(f"{protocol}://{url}:{port}/", new=2, autoraise=True)
        socket.run(app, host=url, port=port)
    except Exception as e:
        print(e)
    print("Hit enter to exit")
    input()