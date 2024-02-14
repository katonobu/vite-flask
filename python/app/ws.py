import time
import sys
import serial
import logging
from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room, rooms, disconnect
from serial.threaded import ReaderThread,LineReader
from serial.tools import list_ports

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PrintLines(LineReader):
    def __init__(self):
        super(PrintLines, self).__init__()
        self.sio = None
        self.event = None
        self.name_space = None
        self.to = None

    def connection_made(self, transport):
        super(PrintLines, self).connection_made(transport)
        self.UNICODE_HANDLING = 'backslashreplace'

    def handle_line(self, data):
        if self.sio is not None and self.event is not None and self.name_space is not None and self.to is not None:
            self.sio.emit(self.event, {'data':{'room':self.to,'rx_data':data}}, namespace=self.name_space, to=self.to)

    def connection_lost(self, exc):
        if exc:
            logger.error(str(exc))

class SerialTransactionNamespace(Namespace):
    serial_obj = {}    
    def __init__(self, namespace, socket):
        super(SerialTransactionNamespace, self).__init__(namespace)
        self.socket = socket
        self.namespace = namespace
    def on_join(self, message):
        rsp_obj = {'rooms':[], 'user_num':-1}
        port = message['room']
        selected_ports = [com_port for com_port in list_ports.comports() if com_port.name.lower() == port.lower()]
        if 1 == len(selected_ports):
            target_port = selected_ports[0].name
            if (target_port in SerialTransactionNamespace.serial_obj) is False:
                try:
                    ser = serial.serial_for_url(target_port, baudrate=115200)
                    t = ReaderThread(ser, PrintLines)
                    t.start()
                    _, protocol = t.connect()
                    protocol.sio = self.socket
                    protocol.event = 'rx_data_notify'
                    protocol.name_space = self.namespace
                    protocol.to = target_port
                    SerialTransactionNamespace.serial_obj.update({target_port:{'serial':ser, 'protocol':protocol, 'thread':t, 'used_count':0}})
                    logger.info(f"open port {target_port}")
                except serial.SerialException as e:
                    logger.info(e)
                    pass
            if target_port in SerialTransactionNamespace.serial_obj:
                current_used_count = SerialTransactionNamespace.serial_obj.get(target_port).get('used_count')
                SerialTransactionNamespace.serial_obj.get(target_port).update({'used_count':current_used_count+1})
                join_room(target_port)
                logger.info(f"Joined {request.sid} to {target_port}")
                rsp_obj.update({'rooms':rooms(),'user_num':SerialTransactionNamespace.serial_obj.get(target_port).get('used_count')})
            else:
                rsp_obj.update({'rooms':rooms()})
        else:
            rsp_obj.update({'rooms':rooms()})
        emit('join_response', {'data': rsp_obj})

    def on_leave(self, message):
        current_used_count = 0
        target_port = message['room']
        if target_port in SerialTransactionNamespace.serial_obj:
            port_obj = SerialTransactionNamespace.serial_obj.get(target_port)
            current_used_count = port_obj.get('used_count')
            if 1 < current_used_count:
                port_obj.update({'used_count':current_used_count-1})
            elif 1 == current_used_count:
                port_obj = SerialTransactionNamespace.serial_obj.pop(target_port)
                port_obj['thread'].close()
                port_obj['serial'].close()
                logger.info(f"close port {target_port}")
            leave_room(target_port)
            logger.info(f"Leaved {request.sid} from {target_port}")
        emit('leave_response', {'data': {'rooms':rooms(), 'user_num':current_used_count-1}})

    def on_send_data(self, message):
        target_port = message['room']
        if target_port in SerialTransactionNamespace.serial_obj:
            port_obj = SerialTransactionNamespace.serial_obj.get(target_port)
            port_obj['protocol'].write_line(message['tx_data'])
            emit('send_data_response', {'data': {'room':message['room'],'tx_data':message['tx_data']}})
            emit('tx_data_notify', {'data': {'room':message['room'],'tx_data':message['tx_data'],'from':request.sid}}, room=message['room'], skip_sid=request.sid)

    def on_set_rts_port(self, message):
        target_port = message['room']
        if target_port in SerialTransactionNamespace.serial_obj:
            port_obj = SerialTransactionNamespace.serial_obj.get(target_port)
            port_obj['serial'].rts = message['requestToSend']
            emit('set_rts_response', {'data': {'room':message['room'],'rts':port_obj['serial'].rts,'from':request.sid}})

    def on_set_dtr_port(self, message):
        target_port = message['room']
        if target_port in SerialTransactionNamespace.serial_obj:
            port_obj = SerialTransactionNamespace.serial_obj.get(target_port)
            port_obj['serial'].dtr = message['dataTerminalReady']
            emit('set_dtr_response', {'data': {'room':message['room'],'dtr':port_obj['serial'].dtr,'from':request.sid}})

    def on_disconnect_request(self, _):
        emit('disconnect_response', {'data': {'msg':'Disconnected!'}}, callback=lambda:disconnect())

    def on_connect(self):
        logger.info(f'Client connected:{request.sid}')

    def on_disconnect(self):
        logger.info(f'Client disconnected:{request.sid}')
