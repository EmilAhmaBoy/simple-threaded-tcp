import socket
import threading
import time

from src.sttcp.server import Server
from src.sttcp.client import Client

server = Server('localhost', 62134)


@server.connection_handler
def server_connection_handler(address: tuple, connection: socket.socket):
    if address[0] == '127.0.0.2':
        print(f'Connection from {":".join(map(str, address))} declined!')
        return False
    print(f'Connected by {":".join(map(str, address))}')
    return True


@server.receive_handler
def server_receive_handler(address: tuple, connection: socket.socket, data: bytes):
    received_string = data.decode('utf-8')
    received_string += '!'
    connection.sendall(received_string.encode('utf-8'))


@server.disconnection_handler
def server_disconnection_handler(address: tuple, reason: Exception):
    print(f'Disconnected by {":".join(map(str, address))}')


@server.universal_handler
def server_universal_handler(handler_type: Server.HandlerType, address: tuple, connection: socket.socket, data: bytes):
    print('- Server', handler_type, sep=': ')
    return True


server.start()

client = Client('localhost', 62134)


@client.connection_handler
def client_connection_handler(address: tuple, connection: socket.socket):
    print(f'Connected to {":".join(map(str, address))}')
    connection.sendall('Meow'.encode('utf-8'))
    return True


@client.response_handler
def client_response_handler(address: tuple, connection: socket.socket, data: bytes):
    response_string = data.decode('utf-8')
    print(f'Received string "{response_string}"')
    if response_string == 'Meow!':
        connection.sendall('Really?'.encode('utf-8'))
        return True
    else:
        return False


@client.disconnection_handler
def client_disconnection_handler(address: tuple, reason: Exception):
    print(f'Disconnected from {":".join(map(str, address))}')


@client.unconnected_handler
def client_unconnected_handler(address: tuple, exception: Exception):
    print(f'Couldn\'t connect to {":".join(map(str, address))}')
    raise exception


@client.universal_handler
def client_universal_handler(handler_type: Server.HandlerType, address: tuple, connection: socket.socket, data: bytes):
    print('- Client', handler_type, sep=': ')
    return True


client.start()


server.keep_alive()
