# -*- coding: utf-8 -*-


from redis import Redis
import time
from datetime import datetime
import uuid
import contextlib
from flask import Flask,request
import random;


app = Flask(__name__)


def update_stats(conn, context, type, value, timeout=5):
    destination = 'stats:%s%s' % (context, type)
    start_key = destination + 'start'
    pipe = conn.pipeline(True)
    end = time.time() + timeout
    while time.time() < end:
        try:
            pipe.watch(start_key)
            now = datetime.utcnow().timetuple()
            hour_start = datetime(*now[:4]).isoformat()

            print "hour_start: " + hour_start

            existing = pipe.get(start_key)
            pipe.multi()
            if existing and existing < hour_start:
                pipe.rename(destination, destination + ':last')
                pipe.rename(start_key, destination + ':pstart')
                pipe.set(start_key, hour_start)

            tkey1 = str(uuid.uuid4())
            tkey2 = str(uuid.uuid4())
            pipe.zadd(tkey1, 'min', value)
            pipe.zadd(tkey2, 'max', value)
            pipe.zunionstore(destination, [destination, tkey1], aggregate='min')
            pipe.zunionstore(destination, [destination, tkey2], aggregate='max')

            pipe.delete(tkey1, tkey2)
            pipe.zincrby(destination, 'count')
            pipe.zincrby(destination, 'sum', value)
            pipe.zincrby(destination, 'sumsq', value*value)

            return pipe.execute()[-3:]
        except Redis.exceptions.WatchError:
            continue


@contextlib.contextmanager
def access_time(conn, context):
    start = time.time()
    yield

    delta = time.time() - start

    stats = update_stats(conn, context, 'AccessTime', delta)

    print stats
    average = stats[1] / stats[0]

    pipe = conn.pipeline(True)
    pipe.zadd('slowest:AccessTime', context, average)
    pipe.zremrangebyrank('slowest:AccessTime', 0, -101)
    pipe.execute()


def process_view(conn, callback):
    with access_time(conn, request.path):
        return callback() # 先执行这里的，再执行yield之后的内容


@app.route('/login', methods=['GET'])
def login():
    conn = Redis()
    process_view(conn, login_logic)

    return "hello world"


def login_logic():
    # login所需要的逻辑
    print "login start "
    print "login end "
    conn = Redis()
    for i in range(1, 100):
        conn.lpush("loginList", "1")

    sleep_time = random.randint(1, 3)
    time.sleep(sleep_time)


@app.route('/logout', methods=['GET'])
def logout():
    conn = Redis()
    process_view(conn, logout_logic)

    return "hello world"


def logout_logic():
    # login所需要的逻辑
    print "logout start "
    print "logout end "
    conn = Redis()
    for i in range(1, 100):
        conn.lpush("loginList", "1")

    sleeptime = random.randint(2, 5)
    time.sleep(sleeptime)

if __name__ == '__main__':
    app.run()



