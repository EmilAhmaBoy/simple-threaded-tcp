import socket
import threading
import traceback
import warnings
import time
from enum import Enum
from typing import Union
try:
    from . import connections, print_sync
except ImportError:
    from sttcp import connections, print_sync


def _default_connection(addr: tuple, connection: socket.socket) -> Union[bool, None]:
    connection.sendall(b'ok')
    return None


def _default_response(addr: tuple, connection: socket.socket, data: bytes):
    print_sync(f'Received "{data.decode("utf-8")}"')
    return False


def _default_disconnection(addr: tuple, reason: Union[None, Exception]):
    pass


def _default_universal(handler_type, addr: Union[tuple, None], connection: Union[socket.socket, None],
                       data: Union[bytes, None]):
    return True


def _default_unconnected(addr: tuple, e: Exception):
    print_sync(f'Couldn\'t connect to {":".join(map(str, addr))}')
    raise e


class Client:
    class DestructionException(ConnectionAbortedError):
        pass

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
        self.sock_name = (self.host, self.port)

        self.is_connected = False

        def client():
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = self._socket
            try:
                s.connect(self.sock_name)
                self.is_connected = True
                self.sock_name = s.getsockname()
                addr = s.getpeername()

                disconnection_reason = None
                data = None
                while True:
                    if data is None:
                        continue_request_alt = self._universal_handler(self.HandlerType.connection, addr, s, None)
                        continue_request = self._connection_handler(addr, s)
                    else:
                        if not self._socket_thread.shutdown:
                            try:
                                continue_request_alt = self._universal_handler(self.HandlerType.response, addr, s, data)
                                continue_request = self._response_handler(addr, s, data)
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
                                s.close()
                                break
                        else:
                            s.close()
                            disconnection_reason = self.DestructionException('Connection closed!')
                            break

                    if self.handler is not None:
                        self.handler(addr, s, data)

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

                self._universal_handler(self.HandlerType.disconnection, addr, None, None)
                self._disconnection_handler(addr, disconnection_reason)

                print_sync(f'Stopped client {":".join(map(str, self.sock_name))}')
            except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, ConnectionError, OSError) \
                    as e:

                self._universal_handler(self.HandlerType.unconnected, None, None, None)
                self._unconnected_handler((self.host, self.port), e)

            s.close()
            self.closed = True
            connections.remove(self)

        self._socket_thread = threading.Thread(target=client, daemon=True)
        self._socket_thread.shutdown = False
        self.closed = False

    def start(self):
        """Starts TCP client"""
        self._socket_thread.start()
        connections.append(self)

    def close(self):
        """Closes TCP client"""
        self._socket_thread.shutdown = True

    def stop(self):
        """Alternative of .close()"""
        self.close()

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

    def keep_alive(self):
        """Use it to make client stoppable only by KeyboardInterrupt exception."""
        try:
            while not self.is_connected:
                pass

            print_sync('Press Ctrl + C to stop client!')

            while self._socket_thread.is_alive():
                self._socket_thread.join(0.1)
        except KeyboardInterrupt:
            if hasattr(self, '_socket'):

                print_sync('Stopping client...')

                self.close()
                while not self.closed:
                    time.sleep(0.1)
