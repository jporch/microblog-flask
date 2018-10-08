from blog_engine import BlogEngine
import json
import uuid
import hashlib
from flask import Flask, abort, make_response, request
app = Flask(__name__)

with open("data/server.json",'r') as f:
    serverConfig = json.load(f)

# Hashing code based of Troy Hunner's examples at https://www.pythoncentral.io/hashing-strings-with-python/
def hash_token(token):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + token.encode()).hexdigest() + ':' + salt
    
def check_token(hashedToken, userToken):
    if hashedToken == "REVOKED":
        return False
    token, salt = hashedToken.split(':')
    return token == hashlib.sha256(salt.encode() + userToken.encode()).hexdigest()

blogConfig = BlogEngine.Config(serverConfig.get("blog_id","blog"))
route = "/"+blogConfig.get("blog_path")
def get_login(request):
    data = request.headers
    login = False
    if data.get("token"):
        for t in range(len(serverConfig["tokens"])):
            if check_token(serverConfig["tokens"][t],data["token"]):
                login = True
    return login
@app.route(route+"/config",methods=['GET'])
def show_config():
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    if get_login(request):
        return json.dumps(blog.config(), indent=2)
    else:
        abort(403)

@app.route(route,methods=['GET'])
def list_posts():
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    return json.dumps(blog.listMessages(showPrivate=get_login(request)), indent=2)

@app.route(route,methods=['POST'])
def new_post():
    if not request.data:
        abort(400)
    if not get_login(request):
        abort(403)
    data = request.get_json(force=True)
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    msg = {
        "title"   : data.get('title',"No Title"),
        "summary" : data.get('summary',""),
        "content" : data.get('content',"Placeholder Content"),
        "tags"    : data.get('tags',""),
        "public"  : data.get('public',0)
    }

    return json.dumps(blog.addMessage(msg), indent=2)

@app.route(route+"/<string:post_id>",methods=['GET'])
def get_post(post_id):
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    post = json.dumps(blog.getMessage(post_id,get_login(request)), indent=2)
    if post == "null":
        abort(404)
    return post

@app.route(route+"/<string:post_id>",methods=['PUT'])
def update_post(post_id):
    data = request.get_json(force=True)
    if not request.data:
        abort(400)
    if not get_login(request):
        abort(403)
    data = request.get_json(force=True)
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    msg = {
        "title"   : data.get('title',None),
        "summary" : data.get('summary',None),
        "content" : data.get('content',None),
        "tags"    : data.get('tags',None),
        "public"  : data.get('public',None)
    }

    return json.dumps(blog.editMessage(post_id,msg), indent=2)

@app.route(route+"/<string:post_id>",methods=['DELETE'])
def delete_post(post_id):
    if not get_login(request):
        abort(403)
    blog = BlogEngine(serverConfig.get("blog_id","blog"))
    blog.deleteMessage(post_id)
    return json.dumps({"Deleted":post_id})


### Error Handling ###
@app.errorhandler(400)
def generic_error(error):
    return make_response(json.dumps({'error': 'Bad stuff', 'request': request.json}), 400)

@app.errorhandler(403)
def forbidden_error(error):
    return make_response(json.dumps({'error': 'Forbidden'}), 403)

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Command line Flask API configuration')
    parser.add_argument('--addToken', nargs=1, help='Add a hashed version of the provided token to the token authorization list.')
    parser.add_argument('--revokeToken', nargs=1, help='Remove the hashed version of the provided token from the token authorization list.')
    args = vars(parser.parse_args())
    
    if (args['addToken']):
        hashedToken = hash_token(args['addToken'][0])
        print(f"Adding token to authorization list: {hashedToken}")
        serverConfig['tokens'].append(hashedToken)
        with open("data/server.json",'w') as f:
            f.write(json.dumps(serverConfig,indent=2))

    elif (args['revokeToken']):
        revokedToken = args['revokeToken'][0]
        print(f"Removing token from authorization list: {revokedToken}")
        tokens = serverConfig['tokens']
        for t in range(len(tokens)):
            if check_token(tokens[t],revokedToken):
                tokens[t] = "REVOKED"
        with open("data/server.json",'w') as f:
            f.write(json.dumps(serverConfig,indent=2))

    else:
        app.run(debug=True)