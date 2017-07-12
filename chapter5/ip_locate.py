import csv
import json
from redis import Redis

def ip_to_score(ip_address):
    score = 0
    for v in ip_address.split('.'):
        if '/' in v:
            tmp = v.split('/')
            v = tmp[0]
            print v
        score = score * 256 + int(v, 10)
    return score


def import_ips_to_redis(conn, filename):
    csv_file = csv.reader(open(filename,'rb'))
    for count, row in enumerate(csv_file):
        start_ip = row[0] if row else ''
        if 'i' in start_ip.lower():
            continue
        if '.' in start_ip:
            start_ip = ip_to_score(start_ip)
        elif start_ip.isdigit():
            start_ip = int(start_ip, 10)
        else:
            continue

        city_id = row[2] + '_' + str(count)
        #conn.zadd('ip2cityid:', city_id, start_ip)

def import_cities_to_redis(conn, filename):
    for row in csv.reader(open(filename, 'rb')):
        if (len(row) < 4 or not row[0].isdigit()):
            continue
        row = [i.decode('latin-1') for i in row]
        city_id = row[0]
        country = row[1]
        region = row[2]
        city = row[3]
        conn.hset('cityid2city:', city_id, json.dumps([city, region, country]))


def find_city_by_ip(conn, ip_address):
    to_find_score = ip_to_score(ip_address)
    ranges = conn.zrangebyscore('ip2cityid',0,to_find_score)
    city_id = ranges[-1]
    print city_id
    city_info = conn.hget('cityid2city:', city_id)
    print city_info

if __name__ == '__main__':
    conn = Redis("127.0.0.1", 6379)
    print conn
    import_ips_to_redis(conn,"/Users/liangchen/Downloads/GeoLite2-City-CSV_20170606/GeoLite2-City-Blocks-IPv4.csv")
    #import_cities_to_redis(conn, "/Users/liangchen/Downloads/GeoLite2-City-CSV_20170606/GeoLite2-City-Locations-en.csv")