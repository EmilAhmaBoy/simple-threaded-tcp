import socket
import threading
import warnings
from enum import Enum
from typing import Union
from . import screen_lock


def _default_connection(addr: tuple, connection: socket.socket):
    connection.sendall(b'ok')


def _default_response(addr: tuple, connection: socket.socket, data: bytes):
    print(f'Received "{data.decode("utf-8")}"')
    return False


def _default_disconnection(addr: tuple):
    pass


def _default_universal(handler_type, addr: Union[tuple, None], connection: Union[socket.socket, None],
                       data: Union[bytes, None]):
    return True


def _default_unconnected(addr: tuple, e: Exception):
    print(f'Couldn\'t connect to {":".join(map(str, addr))}')
    raise e


class Client:
    class HandlerType(Enum):
        connection = 1
        response = 2
        disconnection = 3
        unconnected = 4

    def __init__(self, host: str, port: Union[str, int], handler=None):
        """
        Represents client TCP connection. Add handler using @client.add_handler decorator or server.set_handler(handler)
        function.
        """
        self._connection_handler = _default_connection
        self._response_handler = _default_response
        self._disconnection_handler = _default_disconnection
        self._universal_handler = _default_universal
        self._unconnected_handler = _default_unconnected

        self.handler = handler
        self.host = host
        self.port = port
        self.address = str(self.host) + ':' + str(self.port)

        def client():
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = self._socket
            try:
                s.connect((self.host, self.port))
                addr = s.getpeername()

                data = None
                while True:
                    screen_lock.acquire()
                    if data is None:
                        continue_request_alt = self._universal_handler(self.HandlerType.connection, addr, s, None)
                        continue_request = self._connection_handler(addr, s)
                    else:
                        continue_request_alt = self._universal_handler(self.HandlerType.response, addr, s, data)
                        continue_request = self._response_handler(addr, s, data)

                    if self.handler is not None:
                        self.handler(addr, s, data)

                    screen_lock.release()

                    if continue_request is None:
                        continue_request = continue_request_alt or True

                    if not continue_request:
                        s.close()
                        break

                    try:
                        data = s.recv(1024)
                    except OSError:
                        data = b''

                    if not data:
                        break

                screen_lock.acquire()
                self._universal_handler(self.HandlerType.disconnection, addr, None, None)
                self._disconnection_handler(addr)
                screen_lock.release()
            except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, ConnectionError) as e:
                screen_lock.acquire()
                self._universal_handler(self.HandlerType.unconnected, None, None, None)
                self._unconnected_handler((self.host, self.port), e)
                screen_lock.release()

        self._socket_thread = threading.Thread(target=client)

    def start(self):
        """Starts TCP client"""
        self._socket_thread.start()

    def connection_handler(self, function) -> None:
        """
        Sets a connection handler for TCP client.
        :param function: Function handler parameter with `"address: tuple"`, `"connection: socket.socket"` parameters`
        """
        self._connection_handler = function

    def response_handler(self, function) -> None:
        """
        Sets a reception handler for TCP client.
        :param function: Function handler parameter with `"address: tuple"`, `"connection: socket.socket"`,
        `"data: bytes"` parameters`
        """
        self._response_handler = function

    def disconnection_handler(self, function) -> None:
        """
        Sets a disconnection handler for TCP client.
        :param function: Function handler parameter with `"address: tuple"` parameter`
        """
        self._disconnection_handler = function

    def unconnected_handler(self, function) -> None:
        """
        Sets a disconnection handler for TCP client.
        :param function: Function handler parameter with `"address: tuple"`, `"exception: Exception"` parameters`
        """
        self._unconnected_handler = function

    def universal_handler(self, function) -> None:
        """
        Sets a universal handler for TCP client.
        :param function: Function handler parameter with `"handler_type: sttcp.server.Server.HandlerType"`,
        `"address: tuple"`, `"connection: Union[socket.socket, None]"`, `"data: Union[bytes, None]"` parameters`
        """
        self._universal_handler = function

    def set_handler(self, function):
        """
        Sets a handler for TCP client. Handler format:

        def client_handler(addr: tuple, conn: socket.socket, data: bytes): pass
        """
        self.handler = function
        warnings.warn('This method is deprecated', DeprecationWarning)
