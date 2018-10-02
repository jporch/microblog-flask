import sqlite3
from datetime import datetime
import json
from hashids import Hashids
hashids = Hashids(salt="HideMyIDs",min_length=8,alphabet="abcdefghijklmnopqrstuvwxyz1234567890")

class BlogEngine:
    def __init__(self, blog):
        self.conn = sqlite3.connect(f"data/{blog}.db")

    def showConfig(self):
        c = self.conn.cursor()
        for row in c.execute("SELECT * FROM config;"):
            print(row)

    def initDB(self,config):
        c = self.conn.cursor()        
        with open(config,'r') as f:
            params = json.load(f)
        c.execute("DROP TABLE IF EXISTS config;")
        c.execute("CREATE TABLE config (param, value);")
        c.executemany("INSERT INTO config VALUES (?,?);",params.items())
        
        c.execute("DROP TABLE IF EXISTS messages;")
        c.execute("CREATE TABLE messages (hash text primary key, url unique, title, summary, content, date_published, date_modified, tags, public integer, deleted integer);")
        self.conn.commit()

    def listMessages(self,showDeleted=False):
        c = self.conn.cursor()
        stmnt = "SELECT rowid, * FROM messages;" if showDeleted else "SELECT rowid, * FROM messages WHERE deleted = 0;"

        for row in c.execute(stmnt):
            print(row)

    def addMessage(self,message):
        c = self.conn.cursor()
        c.execute("SELECT MAX(rowid) from messages")
        prevID = c.fetchone()[0] or 0
        newID = hashids.encode(prevID)
        url =  f"jmporch.com/musings/{newID}"
        title = message['title']
        summary = message['summary']
        content = message['content']
        curTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags = message['tags']
        public = message['public']
        newMessage = (newID,url,title,summary, content, curTime, curTime, tags, public)
        c.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,0)",newMessage)
        self.conn.commit()

    def editMessage(self, id, message):
        c = self.conn.cursor()
        curTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE messages SET content = ?, date_modified = ? WHERE hash = ?;", (message, curTime, id))
        self.conn.commit()

    def getMessage(self, id, showDeleted=False):
        c = self.conn.cursor()
        stmnt = "SELECT rowid, * FROM messages WHERE hash = ?;" if showDeleted else "SELECT rowid, * FROM messages WHERE hash = ? AND deleted = 0;"
        for row in c.execute(stmnt,id):
            print(row)

    def deleteMessage(self, id):
        c = self.conn.cursor()
        c.execute("UPDATE messages SET deleted = 1 WHERE hash = ?;",id)
        self.conn.commit()

#CLI intended for debug use, otherwise should be called directly by server
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Lightweight command-line blog framework')
    parser.add_argument('blog', help='ID of the blog, which tells it what database to connect to.')
    parser.add_argument('--init', nargs="?", const="data/blog.json", default="", help='Create a new blog or overwrite existing one (cannot be undone).')
    parser.add_argument('--showConfig', nargs="?", const=True, default=False, help="Outputs the blog's configuration values.")
    parser.add_argument('--listMessages', nargs="?", const=True, default=False, help="Outputs the blog's messages.")
    parser.add_argument('--message', nargs="?", const="Placeholder Text", default="", help='Message to append to the blog feed.')
    parser.add_argument('--getMessage', nargs=1, help="Retrieves the message with the specified ID.")
    parser.add_argument('--editMessage', nargs=2, help="Modifies message with provided ID to have the message passed as the second parameter.")
    parser.add_argument('--deleteMessage', nargs=1, help='Marks message with provided ID as deleted.')
    parser.add_argument('--includeDeleted', nargs="?", const=True, default=False, help="Includes deleted results in output.")

    args = vars(parser.parse_args())


    blog = BlogEngine(args['blog'])

    if (args['init']):
        blog.initDB(args['init'])

    if (args['showConfig']):
        blog.showConfig()

    if (args['message']):
        msg = {
            "title"     : "Testing",
            "summary"   : "Summary Text",
            "content"   : args['message'],
            "tags"      : "tag1,tag2",
            "public"    : "1"
        }
        blog.addMessage(msg)

    if (args['getMessage']):
        blog.getMessage(args['getMessage'],args['includeDeleted'])

    if (args['editMessage']):
        blog.editMessage(args['editMessage'][0],args['editMessage'][1])

    if (args['listMessages']):
        blog.listMessages(args['includeDeleted'])

    if (args['deleteMessage']):
        blog.deleteMessage(args['deleteMessage'])