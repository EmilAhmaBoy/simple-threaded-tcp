# Simple threaded TCP
A module for easy TCP threaded connection.

Installation with pip: `pip install simple-threaded-tcp`

## Example code
```py
import socket

from sttcp.server import Server
from sttcp.client import Client
from sttcp.general import keep_alive
from sttcp import print_sync

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
```

## What's new?
### Version 1.0
- Nothing :)
### Version 1.1
- Now with README.md
### Version 1.2
- Changed `Recieved` to `Received`
- Now `sttcp.client.Client.set_handler` and `sttcp.server.Server.set_handler` are deprecated
- Added new method `sttcp.client.Client.connection_handler`
- Added new method `sttcp.client.Client.response_handler`
- Added new method `sttcp.client.Client.disconnection_handler`
- Added new method `sttcp.client.Client.universal_handler`
- Added new method `sttcp.client.Client.unconnected_handler`
- Added new method `sttcp.server.Server.connection_handler`
- Added new method `sttcp.server.Server.receive_handler`
- Added new method `sttcp.server.Server.disconnection_handler`
- Added new method `sttcp.server.Server.universal_handler`
- Renamed method `sttcp.server.Server.mainloop` to `sttcp.server.Server.keep_alive`
- Added new methods `sttcp.client.Client.start` and `sttcp.server.Server.start`

### Version 1.3
- Added new methods `sttcp.client.Client.close` and `sttcp.server.Server.close`
- Now server handler exceptions don't make server unstoppable by KeyboardInterrupt
- Added new parameter to `disconnection_handler` for both sides - disconnection reason (Union[None, Exception]) 
- Added new exception `sttcp.client.Client.DestructionException`

### Version 1.4
- Added new methods `sttcp.client.Client.stop` and `sttcp.server.Server.stop` as alternatives to `.close`
- Fixed a 100% CPU bug

### Version 1.5
- Now client is stoppable if connection is endless or too long but...
- Now client needs to be `keep_alive`d using `sttcp.client.Client.keep_alive`.
- Added new function `sttcp.general.keep_alive` to `keep_alive` **everything**.
- Added new function `sttcp.print_sync`
#### Version 1.5.1
- Bug fix related to ImportError

## Contacts
Discord: `@emilahmaboy`

that is all :)

## P.s
Sorry for my bad english. I am from Russia, yeah