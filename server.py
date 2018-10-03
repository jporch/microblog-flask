from blog_engine import BlogEngine
import json
from flask import Flask, abort, make_response, request
app = Flask(__name__)


@app.route("/",methods=['GET'])
def show_config():
    blog = BlogEngine("test")
    return json.dumps(blog.config(), indent=2)

@app.route("/posts",methods=['GET'])
def list_posts():
    blog = BlogEngine("test")
    return json.dumps(blog.listMessages(), indent=2)

@app.route("/posts",methods=['POST'])
def new_post():
    data = request.get_json(force=True)
    if not request.data:
        abort(400)
    blog = BlogEngine("test")
    msg = {
        "title"   : data.get('title',"No Title"),
        "summary" : data.get('summary',""),
        "content" : data.get('content',"Placeholder Content"),
        "tags"    : data.get('tags',""),
        "public"  : data.get('public',0)
    }

    return json.dumps(blog.addMessage(msg), indent=2)

@app.route("/posts/<string:post_id>",methods=['GET'])
def get_post(post_id):
    blog = BlogEngine("test")
    return json.dumps(blog.getMessage(post_id), indent=2)

@app.route("/posts/<string:post_id>",methods=['PUT'])
def update_post(post_id):
    data = request.get_json(force=True)
    if not request.data:
        abort(400)
    blog = BlogEngine("test")
    msg = {
        "title"   : data.get('title',None),
        "summary" : data.get('summary',None),
        "content" : data.get('content',None),
        "tags"    : data.get('tags',None),
        "public"  : data.get('public',None)
    }

    return json.dumps(blog.editMessage(post_id,msg), indent=2)

@app.route("/posts/<string:post_id>",methods=['DELETE'])
def delete_post(post_id):
    blog = BlogEngine("test")
    blog.deleteMessage(post_id)
    return json.dumps({"Deleted":post_id})


### Error Handling ###
@app.errorhandler(400)
def generic_error(error):
    return make_response(json.dumps({'error': 'Bad stuff'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)