# このドキュメントをベースに進化させる。
# Flask-SocketIO
#  https://flask-socketio.readthedocs.io/en/latest/index.html

import time
import webbrowser
from flask import Flask
from flask_socketio import SocketIO, emit
from engineio.async_drivers import threading # to avoid runtime error in .exe
from app import serial
from app import static
from app import ws

app = Flask(__name__)
app.register_blueprint(serial.app)
app.register_blueprint(static.app)

socket = SocketIO(
    app,
#    cors_allowed_origins="*",
    async_mode="threading"  # to avoid runtime error in .exe
)

socket.on_namespace(ws.MyCustomNamespace('/'))

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