from redis import Redis
import time
import threading


def notrans():
    conn = Redis("127.0.0.1",6379)
    print conn.incr('notrans:')
    time.sleep(.1)
    conn.incr('notrans:',-1)



def __main__():
    for i in xrange(3):
        threading.Thread(target=notrans).start()
        time.sleep(.5)