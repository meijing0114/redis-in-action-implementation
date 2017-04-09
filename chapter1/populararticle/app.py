# -*- coding: utf-8 -*-

from flask import Flask,request,jsonify
import time
from redis import Redis



app = Flask(__name__)

app.config.from_pyfile('../config/local.py')


@app.route('/user/vote',methods=['POST'])
def vote_article():
    user_id = request.form['user_id']
    article_id = request.form['article_id']
    vote_type = request.form['vote_type']

    conn = Redis()

    cutoff = time.time() - app.config['ONE_WEEK_IN_SECONDS']
    # 超过一周的文章不能再投了 包括支持和反对
    if conn.zscore('time:', article_id) < cutoff:
        return {'code': 100};

    if not conn.get("user:vote:type:" + article_id + user_id):
        conn.sadd('voted:' + vote_type + article_id, user_id)
        if vote_type == "up:":
            # 增加文章的分数
            conn.zincrby('score:', article_id, app.config['VOTE_SCORE'])
            # 增加文章获得的票数
            conn.hincrby("article:detail:" + article_id, 'votes', 1)
            conn.set("user:vote:type:" + article_id + user_id, "up");
        else:
            # 降低文章的分数
            conn.zincrby('score:', article_id, app.config['MINUS_VOTE_SCORE'])
            # 增加文章获得的票数
            conn.hincrby("article:detail:" + article_id, 'votes', -1)
            conn.set("user:vote:type:" + article_id + user_id, "down");
        return {'code': 0};
    else:
        return {'code': -1};

@app.route('/user/flipvote',methods=['POST'])
def flip_vote():
    user_id = request.form['user_id']
    article_id = request.form['article_id']
    conn = Redis()
    # 获取原来是反对还是支持
    vote_type = conn.get("user:vote:type:" + article_id + user_id)

    if vote_type == "up":
        conn.smove(user_id, "vote:up:" + article_id, "vote:down:" + article_id)
        conn.zincrby('score:', article_id, 2 * app.config['MINUS_VOTE_SCORE'])
        # 增加文章获得的票数
        conn.hincrby("article:detail:" + article_id, 'votes', -2)
    elif vote_type == "down":
        conn.smove(user_id, "vote:down:" + article_id, "vote:up:" + article_id)
        conn.zincrby('score:', article_id, 2 * app.config['VOTE_SCORE'])
        # 增加文章获得的票数
        conn.hincrby("article:detail:" + article_id, 'votes', 2)



# 发表一篇文章
@app.route('/article/create',methods=['POST'])
def post_article():
    print request

    user_id = request.form['user_id']
    title = request.form['title']
    link = request.form['link']

    conn = Redis()
    # 生成自增id
    article_id = conn.incrby("article:")

    # 插入文章详情的哈希表
    conn.hset("article:detail:" + article_id, {"title": title, "link": link})

    # 用户加入文章不能投票的黑名单集合中
    conn.sadd("voted:" + article_id, user_id)

    # 加入文章到 存储文章发布时间的有序集合
    conn.zadd("time:", time.time(), article_id)


# 获取文章的列表

@app.route('/article/get',methods=['GET'])
def get_articles():
    order = request.args.get('order', 'score:',type=str)
    page = request.args.get('page',1,type=int)

    print app.config


    conn = Redis()

    start_index = (page - 1) * app.config['ARTICLES_PER_PAGE']
    end_index = page * app.config['ARTICLES_PER_PAGE'] - 1

    article_list = conn.zrevrange(order, start_index, end_index)

    article_detail_list = [];
    for article in article_list:
        article_detail = conn.hgetall("article:detail:" + article)
        article_detail['id'] = article
        article_detail_list.append(article_detail)

    print article_detail_list
    return jsonify(article_detail_list)


# 从群组中添加文章

@app.route('/article/addtogroup',methods=['POST'])
def add_to_groups():
    article_id = request.form['article_id']
    to_add = request.form['to_add']

    conn = Redis()
    for group in to_add:
        conn.sadd("group:" + group, article_id)


# 从群组中删除文章

@app.route('/article/delfromgroup',methods=['POST'])
def del_from_groups():
    article_id = request.form['article_id']
    to_remove = request.form['to_remove']

    conn = Redis()
    for group in to_remove:
        conn.sremove("group" + group, article_id)


# 从群组中根据一定的排序拉取文章, 利用zinterscore的合并作用

@app.route('/article/getfromgroup',methods=['GET'])
def get_from_group():
    group = request.args.get('group', '')
    page = request.args.get('page', '')
    order = request.args.get('order', 'score:')


    key = order + group
    conn = Redis()

    if not conn.exists(key):
        conn.zinterscore(key, ["group:" + group, order], aggregate='max')
        conn.expire(key, 60)
    return get_articles(page, order)

if __name__ == '__main__':
    app.run()