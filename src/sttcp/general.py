import threading

from ..sttcp import connections, screen_lock, print_sync
from .client import Client
from .server import Server
import time


def keep_alive():
    """Use it to make all simple-threaded-tcp connections stoppable only by KeyboardInterrupt"""
    try:
        while True:
            i = 0
            for self in connections:
                if self._socket_thread.is_alive():
                    self._socket_thread.join(0.1)
                else:
                    i += 1
            if i >= len(connections):
                break
    except KeyboardInterrupt:
        for self in connections:
            if hasattr(self, '_socket'):
                _type = 'connection'
                if type(self) is Server:
                    _type = 'server'
                elif type(self) is Client:
                    _type = 'client'

                print_sync(f'Stopping {_type} {":".join(map(str, self.sock_name))}...')

                def close_connection():
                    self.close()
                    while not self.closed:
                        time.sleep(0.1)

                threading.Thread(target=close_connection, daemon=False).start()

    # try:
    #     while not self.is_listening:
    #         pass
    #
    #     print_sync('Press Ctrl + C to stop server!')
    #
    #     while self._socket_thread.is_alive():
    #         self._socket_thread.join(0.1)
    # except KeyboardInterrupt:
    #     if hasattr(self, '_socket'):
    #
    #         print_sync('Stopping server...')
    #
    #         self.close()
    #         while not self.closed:
    #             time.sleep(0.1)
