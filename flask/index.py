#!/usr/bin/python3
from flask import Flask, render_template, request, session
import json
from flask_pymongo import PyMongo

app = Flask(__name__)

app.secret_key = "hoge"

app.config["MONGO_URI"]="mongodb://localhost:27017/testdb"
mongo = PyMongo(app)


import getinfo

@app.route('/')
def index():
    return render_template(
        'search.html',
        title = "ISBN search",
        )

@app.route('/search', methods = ['GET'])
def result():
    query = request.args.get('isbn')
    result = getinfo.search(query)

    if result is False:
        return render_template(
            'error.html',
            query = query
        )
    else:    
        session["isbn"]=query
        session["bookinfo"] =result
        record = mongo.db.data.find_one({"isbn": session["isbn"]})
        if record is not None:
            status = record["status"]
            memo = record.get("memo", "")
        else:
            status = "unread"
            memo = ""

        return render_template(
            'success.html',
            title="search result",
            isbn = query,
            booktitle= result['title'],
            bookauthor = result['author'],
            publisher = result['publisher'],
            status = status,
            memo = memo,
        )

@app.route('/status', methods = ['POST'])
def update_status():
    status = request.form["status"]
    memo = request.form["memo"]
    booktitle= session['bookinfo']["title"]
    bookauthor = session["bookinfo"]['author']
    publisher = session["bookinfo"]['publisher']
    record = { "isbn":session["isbn"], "status": status, "memo": memo}
    print(record)

    mongo.db.data.find_one_and_update(
        {"isbn": session["isbn"]},
        {"$set": {"status": status, 
                "memo": memo,
                "title": booktitle,
                "author": bookauthor,
                "publisher": publisher,
                }
        },
        upsert=True
    )
    return render_template(
        'status.html',
        json = record,
        bookinfo = session["bookinfo"],
        )



if __name__ == "__main__":
    app.run(debug=False)