#!/usr/bin/python3
import requests as req
from flask import Flask
from flask_pymongo import PyMongo
import sys
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
app.config["MONGO_URI"] = "mongodb://localhost:27017/bookmeter"
mongo = PyMongo(app)

req.packages.urllib3.disable_warnings()
req.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'


def isISBN(query):
    if str.isdecimal(query) is True and (len(query) == 10 or len(query) == 13):
        return True
    else:
        return False


def searchNDL(query, forceStrSearch=False, count=3):
    query = str(query)
    if isISBN(query) is False or forceStrSearch is True:
        url = 'https://iss.ndl.go.jp/api/opensearch?' \
            + 'cnt=' + str(count) + '&' \
            + 'title=' + str(query)
        res = req.get(url, verify=False)
        res = BeautifulSoup(res.content, 'lxml')
        tmp =[]
        for i in range(count):
            tmp.append(res.channel.find('item'))
        res = tmp
    elif isISBN(query) is True:
        url = 'https://iss.ndl.go.jp/api/opensearch?' \
            + 'isbn=' + str(query)
        res = req.get(url, verify=False)
        res = BeautifulSoup(res.content, 'lxml',
                            from_encoding='uft-8').channel.find('item')
        
    else:
        res = None
    return res


def bookdb_update(query):
    res = searchNDL(query)
    if res is not None or type(res) != list:
        title = res.find('dc:title').text
        author = res.find('dc:creator').text
        publisher = res.find('dc:publisher').text
        isbn = res.find('dc:identifier').text
        if res.find('dcndl:volume') is not None:  # 本により巻数記載の有無が異なる
            volume = res.find('dcndl:volume').text
        else:
            volume = '1'
        if res.find('dcndl:seriestitle') is not None:
            series = res.find('dcndl:seriestitle').text
        else:
            series = 'None'
        permalink = res.find('guid').text

        mongo.db.bookdb.find_one_and_update(
            {'isbn': isbn},
            {
                "$set":
                {
                    "title": title,
                    "volume": volume,
                    "author": author,
                    "series": series,
                    "publisher": publisher,
                    "permalink": permalink,
                },
            },
            upsert=True
        )
    return res


def bookdb(query):
    if query is None:
        data = 'query is None'
    elif isISBN(query) is not True:
        data = None
    else:  # 書籍情報があるか(MongoDB -> NDL)
        data = mongo.db.bookdb.find_one({'isbn': query})
        if data is None and bookdb_update(query) is None:
            data = 'bookinfo is None'  # NDLでも見つからない場合
        else:
            data = mongo.db.bookdb.find_one({'isbn': query})
    return data


if __name__ == "__main__":
    q = sys.argv[1]
    print(searchNDL(q))
