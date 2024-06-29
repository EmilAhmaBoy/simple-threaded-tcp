import socket

from src.sttcp.server import Server
from src.sttcp.client import Client
from src.sttcp.general import keep_alive
from src.sttcp import print_sync

# Creating a TCP server connector object
server = Server('localhost', 62134)

# Defining connection with client behavior
@server.connection_handler
def server_connection_handler(address: tuple, connection: socket.socket):
    if address[0] == '127.0.0.2':  # address is a (hostname, port) tuple
        print_sync(f'Connection from {":".join(map(str, address))} declined!')  # Using print_sync function to avoid mess in console
        return False  # Declining client (also allowed to use connection.close())
    print_sync(f'Connected by {":".join(map(str, address))}')  # Using print_sync function to avoid mess in console
    return True  # Accepting client

# Defining receiving information from client behavior
@server.receive_handler
def server_receive_handler(address: tuple, connection: socket.socket, data: bytes):
    received_string = data.decode('utf-8')  # Decoding input data
    received_string += '!'
    connection.sendall(received_string.encode('utf-8'))  # Sending encoded string to client

# Defining disconnection behavior
@server.disconnection_handler
def server_disconnection_handler(address: tuple, reason: Exception):
    # Parameter `reason` is new in version 1.3 and means the reason of disconnection
    # This is an Exception that was caught during the handler function execution
    # Also it can be ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError,
    # ConnectionError, OSError
    # Parameter `reason` is None when connection was successful (client requested for connection closure)
    if reason is None:
        print_sync(f'Disconnected by {":".join(map(str, address))}')  # Using print_sync function to avoid mess in console
    else:
        print_sync(f'Disconnected by {":".join(map(str, address))} with reason {reason}')  # Using print_sync function to avoid mess in console

# Defining universal behavior
# It being executed at all request phases like Server.HandlerType.connection, Server.HandlerType.receive etc.
@server.universal_handler
def server_universal_handler(handler_type: Server.HandlerType, address: tuple, connection: socket.socket, data: bytes):
    print_sync('- Server', handler_type, sep=': ')  # Using print_sync function to avoid mess in console
    return True  # If server.connection_handler or something like that is not specified it works instead of them


server.start()  # Launching server (execution started in parallel thread)

# Creating a TCP client connector object
client = Client('localhost', 62134)

# Defining connection with server behavior
@client.connection_handler
def client_connection_handler(address: tuple, connection: socket.socket):
    print_sync(f'Connected to {":".join(map(str, address))}')  # Using print_sync function to avoid mess in console
    # It is required to send anything to server or connection will not finish
    connection.sendall('Meow'.encode('utf-8'))  # Sending encoded string to server
    return True  # Returning True continues connection and awaits for server response

# Defining receiving response from server
@client.response_handler
def client_response_handler(address: tuple, connection: socket.socket, data: bytes):
    response_string = data.decode('utf-8')  # Decoding input data
    print_sync(f'Received string "{response_string}"')  # Using print_sync function to avoid mess in console
    if response_string == 'Meow!':
        connection.sendall('Really?'.encode('utf-8'))  # Sending encoded string to server
        return True  # Continuing connection for awaiting future response
    else:
        return False  # Stopping connection

# Defining disconnection with server behavior
@client.disconnection_handler
def client_disconnection_handler(address: tuple, reason: Exception):
    # Reason parameter is the same as in `server_disconnection_handler`
    print_sync(f'Disconnected from {":".join(map(str, address))}')  # Using print_sync function to avoid mess in console

# Defining exceptions handling behavior
@client.unconnected_handler
def client_unconnected_handler(address: tuple, exception: Exception):
    print_sync(f'Could not connect to {":".join(map(str, address))}')  # ok, there is the same reason...
    raise exception

# Defining universal behavior
@client.universal_handler
def client_universal_handler(handler_type: Server.HandlerType, address: tuple, connection: socket.socket, data: bytes):
    print_sync('- Client', handler_type, sep=': ')  # ...
    return True  # The same as the server universal handler return


client.start()  # Launching client (execution started in parallel thread)


keep_alive()
# keep_alive() is only needed to keep threads alive until KeyboardInterrupt will not be raised
# This is optional in cases of you have something like "while True" statement
# You can also use server.keep_alive() or client.keep_alive() if you have only 1 sttcp connection

"""
Also there are methods like `server.close()` and `client.close()` but they only needed to close a connection.

server.close() awaits for all connections to stop and stops the server
client.close() disconnects the server with the reason of `sttcp.client.Client.DestructionException`
server.stop() and client.stop() are alternatives to server.close() and client.close()
"""