import functools
import redis
import time
import json

CONFIGS = {}


REDIS_CONNECTIONS = {}

def redis_connection(component, wait=1):
    key = 'config:redis:' + component
    def wrapper(function):
        @functools.wraps(function)
        def call(*args, **kwargs):
            old_config = CONFIGS.get(key, object())
            # config_connection 是作为全局的一个配置？
            _config = get_config(
                config_connection, 'redis', component , wait
            )

            config = {}
            for k, v in _config.iteritems():
                config[k.encode('utf-8')] = v

            # 配置变化，重新获取redis的连接
            if config != old_config:
                REDIS_CONNECTIONS[key] = redis.Redis(**config)

            return function(
                REDIS_CONNECTIONS.get(key), *args, **kwargs
            )
        return call
    return wrapper

@redis_connection("logs")
def log_recent(conn, app, message):
    print "conn"

log_recent('main', 'User 235 logged in')

CONFIGS = {}
CHECKED = {}

def get_config(conn, type ,component, wait=1):
    key = 'config:%s:%s'%(type, component)

    if CHECKED.get(key) < time.time() - wait:
        CHECKED[key] = time.time()
        config = json.loads(conn.get(key) or '{}')
        config = dict((str(k), config[k]) for k in config)
        old_config = CONFIGS.get(key)

        if config != old_config:
            CONFIGS[key] = config
    return CONFIGS.get(key)