from blog_engine import BlogEngine
import json
from flask import Flask
app = Flask(__name__)


@app.route("/")
def show_config():
    blog = BlogEngine("test")
    return json.dumps(blog.config(), indent=2)

@app.route("/posts")
def list_messages():
    blog = BlogEngine("test")
    return json.dumps(blog.listMessages(), indent=2)