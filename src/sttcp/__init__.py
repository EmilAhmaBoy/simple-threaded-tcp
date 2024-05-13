import threading

screen_lock = threading.Semaphore(value=1)
