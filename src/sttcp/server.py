import socket
import threading
import traceback
import warnings
import time
from enum import Enum
from typing import Union
from . import screen_lock, connections, print_sync


def _default_connection(addr: tuple, connection: socket.socket) -> Union[bool, None]:
    print_sync(f'Connected by {":".join(map(str, addr))}')
    return None


def _default_receive(addr: tuple, connection: socket.socket, data: bytes):
    pass


def _default_disconnection(addr: tuple, disconnection_reason: Exception):
    print_sync(f'Disconnected by {":".join(map(str, addr))}')


def _default_universal(handler_type, addr: tuple, connection: Union[socket.socket, None], data: Union[bytes, None]):
    return True


class Server:
    class HandlerType(Enum):
        connection = 1
        receive = 2
        disconnection = 3

    def __init__(self, host: str, port: Union[str, int], handler=None):
        """
        Represents server TCP connection. Add handler using @server.add_handler decorator or server.set_handler(handler)
        function.
        """
        self._connection_handler = _default_connection
        self._receive_handler = _default_receive
        self._disconnection_handler = _default_disconnection
        self._universal_handler = _default_universal

        self.handler = handler
        self.host = host
        self.port = port
        self.address = str(self.host) + ':' + str(self.port)
        self.sock_name = (self.host, self.port)

        self.is_listening = False

        def conn_handler(addr, conn: socket.socket):
            with conn:
                disconnection_reason = None
                while True:
                    try:
                        data = conn.recv(1024)
                    except OSError:
                        data = b''

                    if not data:
                        break

                    try:
                        self._universal_handler(self.HandlerType.receive, addr, conn, data)
                        self._receive_handler(addr, conn, data)
                        if self.handler is not None:
                            self.handler(addr, conn, data)
                    except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError,
                            ConnectionError, OSError) as e:
                        disconnection_reason = e
                        break
                    except Exception as e:
                        message = ('\033[91mOh no! Something went wrong in your handler! Check it out and find '
                                   'problems:\033[0m')
                        message += '\n' + traceback.format_exc()
                        message += '\n' + '\033[91mDisconnecting the client\033[0m'
                        print_sync(message)
                        disconnection_reason = e
                        conn.close()
                        break

                try:
                    self._universal_handler(self.HandlerType.disconnection, addr, None, None)
                    self._disconnection_handler(addr, disconnection_reason)
                except Exception:
                    message = ('\033[91mOh no! Something went wrong in your handler! Check it out and find '
                               'problems:\033[0m')
                    message += '\n' + traceback.format_exc()
                    print_sync(message)

        def server():
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = self._socket
            s.bind(self.sock_name)
            self.sock_name = s.getsockname()
            s.listen()

            print_sync(f'Listening to {":".join(map(str, s.getsockname()))}')

            self.is_listening = True
            while not self._socket_thread.shutdown:
                try:
                    conn, addr = s.accept()
                    if addr != self._socket_thread.shutdown_socket:

                        try:
                            connect_alt = self._universal_handler(self.HandlerType.connection, addr, None, None)
                            connect = self._connection_handler(addr, conn)
                        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError,
                                ConnectionError, OSError):
                            continue

                        if connect is None:
                            connect = connect_alt or True

                        if connect:
                            conn_thread = threading.Thread(target=conn_handler, args=(addr, conn))
                            conn_thread.start()
                        else:
                            conn.close()
                except OSError:
                    break

            print_sync(f'Stopped server {":".join(map(str, self.sock_name))}')

            s.close()
            self.closed = True
            connections.remove(self)

        self._socket_thread = threading.Thread(target=server, daemon=True)
        self._socket_thread.shutdown = False
        self._socket_thread.shutdown_socket = None
        self.closed = False

    def start(self):
        """Starts TCP server"""
        self._socket_thread.start()
        connections.append(self)

    def close(self):
        """Closes TCP server"""
        self._socket_thread.shutdown = True
        try:
            closure_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            closure_socket.connect((self.host, self.port))
            self._socket_thread.shutdown_socket = closure_socket.getsockname()
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, ConnectionError, OSError) as e:
            raise e

    def stop(self):
        """Alternative of .close()"""
        self.close()

    def set_handler(self, function):
        """
        Sets a handler for TCP server. Handler format:

        def server_handler(addr: tuple, conn: socket.socket, data: bytes): pass
        """
        self.handler = function
        warnings.warn('This method is deprecated', DeprecationWarning)

    def connection_handler(self, function) -> None:
        """
        Sets a connection handler for TCP server.
        :param function: Function handler parameter with `"address: tuple"`, `"connection: socket.socket"` parameters`
        """
        self._connection_handler = function

    def receive_handler(self, function) -> None:
        """
        Sets a reception handler for TCP server.
        :param function: Function handler parameter with `"address: tuple"`, `"connection: socket.socket"`,
        `"data: bytes"` parameters`
        """
        self._receive_handler = function

    def disconnection_handler(self, function) -> None:
        """
        Sets a disconnection handler for TCP server.
        :param function: Function handler parameter with `"address: tuple"` parameter`
        """
        self._disconnection_handler = function

    def universal_handler(self, function) -> None:
        """
        Sets a universal handler for TCP server.
        :param function: Function handler parameter with `"handler_type: sttcp.server.Server.HandlerType"`,
        `"address: tuple"`, `"connection: Union[socket.socket, None]"`, `"data: Union[bytes, None]"` parameters`
        """
        self._universal_handler = function

    def keep_alive(self):
        """Use it to make server stoppable only by KeyboardInterrupt exception."""
        try:
            while not self.is_listening:
                pass

            print_sync('Press Ctrl + C to stop server!')

            while self._socket_thread.is_alive():
                self._socket_thread.join(0.1)
        except KeyboardInterrupt:
            if hasattr(self, '_socket'):

                print_sync('Stopping server...')

                self.close()
                while not self.closed:
                    time.sleep(0.1)

    def mainloop(self):
        warnings.warn('This method was renamed to keep_alive', DeprecationWarning)
        self.keep_alive()
