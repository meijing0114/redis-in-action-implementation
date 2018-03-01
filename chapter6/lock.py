import uuid
import time
import redis
import math
from redis import Redis

from flask import Flask,request


app = Flask(__name__)

@app.route('/watch/test',methods=['GET'])
def watch_test():
    conn = Redis("127.0.0.1", 6379)
    pipe = conn.pipeline(True)

    while(1):
        try:
            pipe.watch("user")
            #print "user watched"
            pipe.incr("other",1)
            pipe.multi()
            pipe.incr("user",1)
            #print "multi success"
            pipe.execute()
            pipe.unwatch()
            #print "user unwatched"
            break;

        except redis.exceptions.WatchError:
            print "watch exception"
            pass
    return "0";


def acquire_lock(conn, lockname, acquire_timeout=10):
    identifier = str(uuid.uuid4())

    end = time.time() + acquire_timeout
    while time.time() < end:
        if conn.setnx('lock:' + lockname, identifier):
            return identifier

        time.sleep(.001)

    return False


def release_lock(conn, lockname, indentifier):
    pipe = conn.pipeline(True)
    lockname = 'lock:' + lockname

    while True:
        try:
            pipe.watch(lockname)
            if pipe.get(lockname) == indentifier:
                pipe.multi()
                pipe.delete(lockname)
                pipe.execute()
                return True
            pipe.unwatch()
            break

        except redis.exceptions.WatchError:
            pass

    return False


def purchase_item_with_market_lock(conn, buyerid, itemid, sellerid):
    buyer = "users:%s"%buyerid
    seller = "users:%s"%sellerid
    item = "%s.%s"%(itemid, sellerid)
    inventory = "inventory:%s"%buyerid

    locked = acquire_lock(conn, "market")

    if locked == False:
        return False

    pipe = conn.pipeline(True)
    try:
        pipe.zscore("market:", item)
        pipe.hget(buyer, 'funds')
        price, funds = pipe.execute()
        if price is None or price > funds:
            return None

        pipe.hincrby(seller, 'funds', int(price))
        pipe.hincrby(buyer, 'funds', int(-price))
        pipe.sadd(inventory, item)
        pipe.zrem("market:", item)
        pipe.execute()
        return True

    finally:
        release_lock(conn, "market", locked)


def acquire_lock_with_timeout(
    conn, lockname, acquire_timeout=10, lock_timeout=10):
    identifier = str(uuid.uuid4())                      #A
    lockname = 'lock:' + lockname
    lock_timeout = int(math.ceil(lock_timeout))         #D

    end = time.time() + acquire_timeout
    while time.time() < end:
        if conn.setnx(lockname, identifier):            #B
            conn.expire(lockname, lock_timeout)         #B
            return identifier
        elif conn.ttl(lockname) < 0:                    #C
            conn.expire(lockname, lock_timeout)         #C

        time.sleep(.001)

    return False

if __name__ == '__main__':
    app.run()