import logging
import webbrowser
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from engineio.async_drivers import threading # to avoid runtime error in .exe
from app import serial
from app import static
from app import ws

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.register_blueprint(serial.app)
app.register_blueprint(static.app)
CORS(app, resources={r'/ports/*': {'origins': ['http://localhost:5173','http://localhost:5001'] }})
socket = SocketIO(
    app,
    cors_allowed_origins=['http://localhost:5173', 'http://localhost:5001'],
    async_mode="threading"  # to avoid runtime error in .exe
)
namespace = '/serialtransaction'
serialTransactionNamespace = ws.SerialTransactionNamespace(namespace, socket)
socket.on_namespace(serialTransactionNamespace)

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