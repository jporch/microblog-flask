import sqlite3
from datetime import datetime
import json
from hashids import Hashids

class BlogEngine:
    def __init__(self, blogID):
        configData = BlogEngine.Config(blogID)
        hashSalt = configData.get("id_salt","HashSecretSalt")
        self.conn = sqlite3.connect(f"data/{blogID}.db")
        self.hashids = Hashids(salt=hashSalt,min_length=8,alphabet="abcdefghijklmnopqrstuvwxyz1234567890")
    
    @staticmethod
    def messageFromRow(row):
        return {
            "hash"           : row[0],
            "url"            : row[1],
            "title"          : row[2],
            "summary"        : row[3],
            "content"        : row[4],
            "date_published" : row[5],
            "date_modified"  : row[6],
            "tags"           : row[7],
            "public"         : row[8],
            "deleted"        : row[9]
        }

    @staticmethod
    def Config(blogID):
        c = sqlite3.connect(f"data/{blogID}.db").cursor()
        configData = {}
        for row in c.execute("SELECT * FROM config;"):
            configData[row[0]] = row[1]
        return configData

    def config(self):
        c = self.conn.cursor()
        configData = {}
        for row in c.execute("SELECT * FROM config;"):
            configData[row[0]] = row[1]
        return configData

    @staticmethod
    def initDB(configJSON="data/blog.json"):
        with open(configJSON,'r') as f:
            params = json.load(f)
        blogID = params.get("blog_id","blog")
        c = sqlite3.connect(f"data/{blogID}.db").cursor()
        c.execute("DROP TABLE IF EXISTS config;")
        c.execute("CREATE TABLE config (param, value);")
        c.executemany("INSERT INTO config VALUES (?,?);",params.items())

        c.execute("DROP TABLE IF EXISTS messages;")
        c.execute("CREATE TABLE messages (hash text primary key, url unique, title, summary, content, date_published, date_modified, tags, public integer, deleted integer);")
        c.connection.commit()

    def listMessages(self,showDeleted=False):
        c = self.conn.cursor()
        stmnt = "SELECT * FROM messages;" if showDeleted else "SELECT * FROM messages WHERE deleted = 0;"
        messages = []
        for row in c.execute(stmnt):            
            messages.append(BlogEngine.messageFromRow(row))
        return messages

    def addMessage(self,message):
        c = self.conn.cursor()
        c.execute("SELECT MAX(rowid) from messages")
        prevID = c.fetchone()[0] or 0
        newID = self.hashids.encode(prevID)
        url =  f"jmporch.com/musings/{newID}"
        title = message.get('title')
        summary = message.get('summary')
        content = message.get('content')
        curTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags = message.get('tags')
        public = message.get('public',0)
        newMessage = (newID,url,title,summary, content, curTime, curTime, tags, public)
        c.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,0)",newMessage)
        self.conn.commit()
        return self.getMessage(newID)

    def editMessage(self, id, message):
        c = self.conn.cursor()
        c.execute("UPDATE messages SET date_modified = ? WHERE hash = ?;", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),id))
        if message.get('title'):
            c.execute("UPDATE messages SET title = ? WHERE hash = ?;", (message.get('title'),id))
        if message.get('summary'):
            c.execute("UPDATE messages SET summary = ? WHERE hash = ?;", (message.get('summary'),id))
        if message.get('content'):
            c.execute("UPDATE messages SET content = ? WHERE hash = ?;", (message.get('content'),id))
        if message.get('tags'):
            c.execute("UPDATE messages SET tags = ? WHERE hash = ?;", (message.get('tags'),id))
        if message.get('public'):
            c.execute("UPDATE messages SET public = ? WHERE hash = ?;", (message.get('public'),id))

        self.conn.commit()
        return self.getMessage(id)

    def getMessage(self, id, showDeleted=False):
        c = self.conn.cursor()
        stmnt = "SELECT * FROM messages WHERE hash = ?;" if showDeleted else "SELECT * FROM messages WHERE hash = ? AND deleted = 0;"
        for row in c.execute(stmnt,(id,)):
            return BlogEngine.messageFromRow(row)

    def deleteMessage(self, id):
        c = self.conn.cursor()
        c.execute("UPDATE messages SET deleted = 1 WHERE hash = ?;",(id,))
        self.conn.commit()

        return self.getMessage(id)

#CLI intended for debug use, otherwise should be called directly by server
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Lightweight command-line blog framework')
    parser.add_argument('blogID', help='ID of the blog, which tells it what database to connect to.')
    parser.add_argument('--init', nargs="?", const="data/blog.json", default="", help='Create a new blog or overwrite existing one (cannot be undone).')
    parser.add_argument('--showConfig', nargs="?", const=True, default=False, help="Outputs the blog's configuration values.")
    parser.add_argument('--listMessages', nargs="?", const=True, default=False, help="Outputs the blog's messages.")
    parser.add_argument('--message', nargs="?", const="Placeholder Text", default="", help='Message to append to the blog feed.')
    parser.add_argument('--getMessage', nargs=1, help="Retrieves the message with the specified ID.")
    parser.add_argument('--editMessage', nargs=2, help="Modifies message with provided ID to have the message passed as the second parameter.")
    parser.add_argument('--deleteMessage', nargs=1, help='Marks message with provided ID as deleted.')
    parser.add_argument('--includeDeleted', nargs="?", const=True, default=False, help="Includes deleted results in output.")

    args = vars(parser.parse_args())

    if (args['init']):
        print(f"Creating blog from {args['init']}.")
        BlogEngine.initDB(args['init'])

    blog = BlogEngine(args['blogID'])

    if (args['showConfig']):
        print("Blog config:")
        print(blog.config())

    if (args['message']):
        msg = json.loads(args['message'])
        print("Added new message:")
        print(blog.addMessage(msg))

    if (args['getMessage']):
        print(f"Retrieving message {args['getMessage']}:")
        print(blog.getMessage(args['getMessage'],args['includeDeleted']))

    if (args['editMessage']):
        print(f"Edited message {args['editMessage']}:")
        print(blog.editMessage(args['editMessage'][0],args['editMessage'][1]))

    if (args['listMessages']):
        print("List of all messages:")
        print(blog.listMessages(args['includeDeleted']))

    if (args['deleteMessage']):
        print("Deleted message:")
        print(blog.deleteMessage(args['deleteMessage']))