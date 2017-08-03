import bisect
import uuid
from redis import Redis
import redis
from flask import Flask,request
import  json


app = Flask(__name__)


valid_characters = '`abcdefghijklmnopqrstuvwxyz{'

def find_prefix_range(prefix):
    posn = bisect.bisect_left(valid_characters, prefix[-1:])
    suffix = valid_characters[(posn or 1) - 1]
    return prefix[:-1] + suffix + '{', prefix + '{'

def autocomplete_on_prefix(conn, guild, prefix):
    start, end = find_prefix_range(prefix)
    identifier = str(uuid.uuid4())
    start += identifier
    end += identifier
    zset_name = 'members:' + guild

    conn.zadd(zset_name, start , 0 , end, 0)
    pipeline = conn.pipeline(True)
    while 1:
        try:
            pipeline.watch(zset_name)
            sindex = pipeline.zrank(zset_name, start)
            eindex = pipeline.zrank(zset_name, end)
            erange = min(sindex + 9, eindex - 2)
            print "sindex:" + sindex + "eindex:" + eindex + "erange:" + erange
            pipeline.multi()
            pipeline.zrem(zset_name, start, end)
            pipeline.zrange(zset_name, sindex, erange)
            items = pipeline.execute()[-1]
            break
        except redis.exceptions.WatchError:
            continue

    return [item for item in items if '{' not in item]

@app.route('/join_guild', methods=['POST'])
def join_guild():
    guild = request.form['guild']
    user = request.form['user']

    print "guild:" + guild + " user:" + user

    conn = Redis("127.0.0.1",6379)
    ret = conn.zadd('members:' + guild, user, 0)

    return "0"

@app.route('/leave_guild',methods=['POST'])
def leave_guild():
    guild = request.form['guild']
    user = request.form['user']

    conn = Redis("127.0.0.1",6379)
    conn.zrem('members:' + guild, user)

    return "0"


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    keyword = request.args.get('keyword')
    guild = request.args.get('guild')

    conn = Redis("127.0.0.1", 6379)
    list = autocomplete_on_prefix(conn, guild, keyword)

    print list

    return  json.dump(list)

if __name__ == '__main__':
    app.run()

