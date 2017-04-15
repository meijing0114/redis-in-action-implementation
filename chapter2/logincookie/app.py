from flask import Flask

app = Flask(__name__)


'''
使用token类型的cookie进行登陆态的保持
看能支持多少个人同时在线？
'''

@app.route('/check_login')
# 检查当前的登录状态
def check_login():
    return 'Hello World!'


@app.route('/update_login_status')
# 更新登录状态,访问页面时进行登陆态的需求
def update_login_status():
    return 'Hello World!'

# 登出，清除session，清除购物车
@app.route('/logout')
def logout():
    return 'logout'

'''
购物车的商品管理

'''

# 商品加入购物车


# 商品从购物车移除，单个的操作


# 缓存页面数据，只缓存最热门的10000个商品，使用有序集合存储商品的浏览量。每五分钟，去掉20000名之后的，
# 并且之前的访问次数全部除以二。或者乘以一个和时间负相关的参数。



# 定期缓存数据库中的行数据,保证缓存中读取到剩余的库存量

if __name__ == '__main__':
    app.run()
