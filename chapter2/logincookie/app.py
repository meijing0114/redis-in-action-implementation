from flask import Flask

app = Flask(__name__)


@app.route('/check_login')
# 检查当前的登录状态
def check_login():
    return 'Hello World!'


@app.route('/update_login_status')
# 更新登录状态
def update_login_status():
    return 'Hello World!'

# 登出
@app.route('/logout')
def logout():
    return 'logout'

if __name__ == '__main__':
    app.run()
