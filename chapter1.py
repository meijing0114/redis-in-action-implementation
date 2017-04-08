import time;
import redis;

ONE_WEEK_IN_SECONDS = 7*86400
VOTE_SCORE = 432

# 数据结构：
# 一个存储文章分数的有序集合
# 一个存储文章发布时间的有序集合
# 一个存储每篇文章投票用户的集合，一个用户只能投票一次
# 一个存储文章详情的哈希表，包括title link poster time votes字段

# 用户对一篇文章投票
def article_vote(conn, user, article_id):
    cutoff = time.time() - ONE_WEEK_IN_SECONDS
    # 超过一周的文章不能再投了
    if conn.zscore('time:',article_id) < cutoff:
        return

    if conn.sadd('voted:'+article_id, user):
        # 增加文章的分数
        conn.zincrby('score:',article_id,VOTE_SCORE)
        # 增加文章获得的票数
        conn.hincrby("article:detail:"+article_id,'votes',1)

# 发表一篇文章
def post_article(conn, user, title,link):
    # 生成自增id
    article_id = conn.incrby("article:")

    # 插入文章详情的哈希表
    conn.hset("article:detail:"+article_id,{"title" : title, "link":link})

    # 用户加入文章不能投票的黑名单集合中
    conn.sadd("voted:"+article_id,user)

    # 加入文章到 存储文章发布时间的有序集合
    conn.zadd("article:orderbytime",time.time(),article_id)

ARTICLES_PER_PAGE = 25
# 获取文章的列表
def get_articles (conn, page , order='score:'):
    start_index = (page-1)*ARTICLES_PER_PAGE
    end_index = page*ARTICLES_PER_PAGE -1

    article_list = conn.zrevrange(order,start_index,end_index)

    article_detail_list = [];
    for article in article_list:
        article_detail = conn.hgetall("article:detail:"+article)
        article_detail['id'] = article
        article_detail_list.append(article_detail)

    print article_detail_list
    return article_detail_list

def add_to_groups(conn,article_id,to_add=[]):
    

def remove_from_groups(conn, article_id, to_add=[]):
