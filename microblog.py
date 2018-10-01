import sqlite3
from datetime import datetime
import argparse
import json
from hashids import Hashids
hashids = Hashids(salt="HideMyIDs",min_length=8,alphabet="abcdefghijklmnopqrstuvwxyz1234567890")

parser = argparse.ArgumentParser(description='Lightweight command-line blog framework')
parser.add_argument('blog', help='ID of the blog, which tells it what database to connect to.')
parser.add_argument('--init', nargs="?", const="data/blog.json", default="", help='Create a new blog or overwrite existing one (cannot be undone).')
parser.add_argument('--message', nargs="?", const="Placeholder Text", default="", help='Message to append to the blog feed.')
parser.add_argument('--showConfig', nargs="?", const=True, default=False, help="Outputs the blog's configuration values.")
parser.add_argument('--getMessage', nargs=1, help="Retrieves the message with the specified ID.")
parser.add_argument('--listMessages', nargs="?", const=True, default=False, help="Outputs the blog's messages.")
args = vars(parser.parse_args())

def connectToBlog(name):
    return sqlite3.connect(f"data/{name}.db")

def showConfig():
    global conn
    c = conn.cursor()

    for row in c.execute("SELECT * FROM config;"):
        print(row)

def initDB(config):
    global conn
    c = conn.cursor()
    
    with open(config,'r') as f:
        params = json.load(f)

    c.execute("DROP TABLE IF EXISTS config;")
    c.execute("CREATE TABLE config (param, value);")
    c.executemany("INSERT INTO config VALUES (?,?);",params.items())
    
    c.execute("DROP TABLE IF EXISTS messages;")
    c.execute("CREATE TABLE messages (hash, url unique, title, summary, content, date_published, date_modified, tags, public integer, deleted integer);")
    conn.commit()

def addMessage(message):
    global conn
    c = conn.cursor()
    c.execute("SELECT MAX(rowid) from messages")
    prevID = c.fetchone()[0] or 0
    newID = hashids.encode(prevID + 1)
    url =  f"jmporch.com/musings/{newID}"
    title = "Some Title"
    summary = "Summary" 
    curTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tags = ""
    public = 1
    newMessage = (newID,url,title,summary, message, curTime, curTime, tags, public)
    c.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,0)",newMessage)
    conn.commit()

def getMessage():
    global conn
    global args
    c = conn.cursor()
    for row in c.execute("SELECT rowid, * FROM messages WHERE hash=?;",args['getMessage']):
        print(row)

def listMessages():
    global conn
    c = conn.cursor()
    
    for row in c.execute("SELECT rowid, * FROM messages;"):
        print(row)

conn = connectToBlog(args['blog'])

if (args['init']):
    initDB(args['init'])

if (args['message']):
    addMessage(args['message'])

if (args['showConfig']):
    showConfig()

if (args['getMessage']):
    getMessage()

if (args['listMessages']):
    listMessages()