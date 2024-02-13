import time
from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect

class SerialTransactionNamespace(Namespace):
    def on_join(self, message):
        join_room(message['room'])
        emit('my_response', {'data': rooms()})

    def on_leave(self, message):
        leave_room(message['room'])
        emit('my_response', {'data': rooms()})

    def on_close_room(self, message):
        emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.'}, room=message['room'])
        close_room(message['room'])

    def on_my_room_event(self, message):
        emit('my_response', {'data': message['data']}, room=message['room'])

    def on_disconnect_request(self):
        emit('my_response', {'data': 'Disconnected!'})
        disconnect()

    def on_ping(self, data):
        print(data)
        print(time.time())
        emit("pong", str(time.time()))

    def on_connect(self):
        print('Client connected', request.sid)

    def on_disconnect(self):
        print('Client disconnected', request.sid)
