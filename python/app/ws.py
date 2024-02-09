import time
from flask_socketio import Namespace, emit

class MyCustomNamespace(Namespace):
    def on_ping(self, data):
        print("MyCustomNamespace")
        print(data)
        print(time.time())
        emit("pong", str(time.time()))

