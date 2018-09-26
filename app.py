import flask, sqlite3, click, logging, json, datetime
from flask import Flask, request, jsonify, Response
from flask_basicauth import BasicAuth


app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum.db'

class dbAuth(BasicAuth):
    def check_credentials(this, username, password):
        app.config["username"] = username
        return is_valid_user(username, password)

def is_valid_user(username, password):
    query = "SELECT EXISTS (SELECT * FROM users WHERE username='%s' AND password='%s');" % (username, password)
    result = query_db(query)

    if (result[0].values() == [0]):
        app.logger.info("Access Denied")
        return False
    else:
        return True

basicAuth = dbAuth(app)

## exception handler

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

## Home page
@app.route('/', methods=['GET'])
def home():
    return "<h1>Discussion Forum API</h1><p>This site is a prototype API for a discussion forum.</p>"


## HTTP GET methods
@app.route('/forums', methods=['GET'])
def forums_all():
    all_forums = query_db('SELECT * FROM forums;')
    return jsonify(all_forums)

@app.route('/forums/<forum_id>', methods=['GET'])
def filter_forum(forum_id):
    forum = query_db("SELECT thread_id, title, creator, timestamp FROM threads WHERE forum_id=%s ORDER BY strftime(timestamp) DESC;" % forum_id) #need to do reverse chron order
    return jsonify(forum)

@app.route('/forums/<forum_id>/<thread_id>', methods=['GET'])
def filter_thread(forum_id, thread_id):
    thread = query_db("SELECT author, text, timestamp FROM posts WHERE forum_id=%s AND thread_id=%s ORDER BY strftime(timestamp);" % (forum_id, thread_id)) #reverse chron
    return jsonify(thread)

## HTTP POST methods
@app.route('/forums', methods = ['POST'])
@basicAuth.required
def create_forum():
    reqJSON = request.get_json()
    forum_exists = existsInDB("SELECT EXISTS (SELECT * FROM forums WHERE name='%s');" % reqJSON.get('name').replace("'", "''"))

    if(forum_exists):
        raise InvalidUsage('http 409 conflict', status_code=409)
    else:
        query_db("INSERT INTO forums(name, creator) VALUES('%s', '%s');" % (reqJSON.get('name').replace("'", "''"), app.config['username']))
        resp = Response('{"message": "Successfully Created"}', mimetype='application/json')
        forum_path = "/forums/%s" % getLatestID()
        resp.headers['Location'] = forum_path
        return resp

@app.route('/forums/<forum_id>', methods = ['POST'])
@basicAuth.required
def create_thread(forum_id):
    reqJSON = request.get_json()
    forum_exists = existsInDB("SELECT EXISTS (SELECT * FROM forums WHERE forum_id=%s);" % forum_id)

    if(not forum_exists):
        raise InvalidUsage('HTTP 404 Not Found', status_code=404)
    else:
        timestamp = getTimestamp()
        query_db("INSERT INTO threads(title, creator, timestamp, forum_id) VALUES('%s', '%s', '%s', %s);" % (reqJSON.get('title').replace("'", "''"), app.config['username'], timestamp, forum_id))
        thread_id = getLatestID()
        query_db("INSERT INTO posts (author, text, timestamp, thread_id, forum_id) VALUES('%s', '%s', '%s', %s, %s);" % (app.config['username'], reqJSON.get('text').replace("'", "''"), timestamp, thread_id, forum_id))
        resp = Response('{"message": "Successfully Created"}', mimetype='application/json')
        resp.headers['Location'] = "/forums/%s/%s" % (forum_id, thread_id)
        return resp

@app.route('/forums/<forum_id>/<thread_id>', methods = ['POST'])
@basicAuth.required
def create_post(forum_id, thread_id):
    reqJSON = request.get_json()
    thread_exists = existsInDB("SELECT EXISTS (SELECT * FROM threads WHERE forum_id='%s' AND thread_id='%s');" % (forum_id, thread_id))

    if(not thread_exists):
        raise InvalidUsage('HTTP 404 Not Found', status_code=404)
    else:
        timestamp = getTimestamp()
        query_db("INSERT INTO posts (author, text, timestamp, thread_id, forum_id) VALUES('%s', '%s', '%s', '%s', '%s');" % (app.config['username'], reqJSON.get('text').replace("'", "''"), timestamp, thread_id, forum_id))
        resp = Response('{"message": "Successfully Created"}', mimetype='application/json')
        resp.headers['Location'] = "/forums/%s/%s" % (forum_id, thread_id)
        return resp

@app.route('/users', methods = ['POST'])
def create_user():
    reqJSON = request.get_json()
    user_exists = existsInDB("SELECT EXISTS (SELECT * FROM users WHERE username='%s');" % reqJSON.get('username').replace("'", "''"))

    if(user_exists):
        raise InvalidUsage('HTTP 409 Conflict', status_code=409)
    else:
        query_db("INSERT INTO users VALUES('%s', '%s');" % (reqJSON.get('username').replace("'", "''"), reqJSON.get('password').replace("'", "''")))
        resp = Response('{"message": "Successfully Created"}', mimetype='application/json')
        return resp

def existsInDB(query):
    result = query_db(query)
    return result[0].values()[0]

def getLatestID():
    id = query_db("SELECT last_insert_rowid()")
    return id[0].values()[0]

def getTimestamp():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")

## HTTP PUT methods
@app.route('/users/<username>', methods = ['PUT'])
@basicAuth.required
def change_password(username):
    reqJSON = request.get_json()
    username_exists = existsInDB("SELECT EXISTS (SELECT * FROM users WHERE username='%s');" % reqJSON.get('username'))

    if(not username_exists):
        raise InvalidUsage('HTTP 404 Not Found', status_code=404)
    elif(app.config["username"] != reqJSON.get('username')):
        raise InvalidUsage('HTTP 409 Conflict', status_code=409)
    else:
        query_db("UPDATE users SET password = '%s' WHERE username='%s'" % (reqJSON.get('password') , reqJSON.get('username')))
        resp = Response('{"message": "Successfully Updated"}', mimetype='application/json')
        return resp

## Resource path not valid
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not b e found.</p>", 404


## Database helper functions
def get_db():
    db = getattr(Flask, '_database', None)
    if db is None:
        db = Flask._database = sqlite3.connect(DATABASE)
    return db

def init():
    with app.app_context():
        db = get_db()
        with app.open_resource('init.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_db(query):
    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    result = cur.execute(query).fetchall()
    conn.commit()
    return result


## Custom CLI command
@app.cli.command()
def init_db():
    init()


if __name__ == "__main__":
    app.run()
