import threading

screen_lock = threading.Semaphore(value=1)

old_print = print


def print_sync(*args, **kwargs):
    screen_lock.acquire()
    old_print(*args, **kwargs)
    screen_lock.release()


connections = []
