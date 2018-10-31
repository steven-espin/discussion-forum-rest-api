import flask, sqlite3, click, logging, json, datetime, uuid, sys, cmd
from flask import Flask, request, jsonify, Response, g
from flask_basicauth import BasicAuth

sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum1.db'
SHARD1 = 'forum2.db'
SHARD2 = 'forum3.db'
SHARD3 = 'forum4.db'

## Basic authentication
class dbAuth(BasicAuth):
    def check_credentials(this, username, password):
        app.config["username"] = username
        user_esists = existsInDB("SELECT EXISTS (SELECT * FROM users WHERE username='%s' AND password='%s');" % (username, password))

        if (not user_esists):
            raise InvalidUsage('401 UNAUTHORIZED', status_code=401)
        else:
            return True

basicAuth = dbAuth(app)

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
    forum = query_db("SELECT thread_id, title, creator, timestamp FROM threads WHERE forum_id=%s ORDER BY strftime(timestamp) DESC;" % forum_id)
    if not forum:
        raise InvalidUsage('HTTP 404 Not Found', status_code=404)
    return jsonify(forum)

@app.route('/forums/<forum_id>/<thread_id>', methods=['GET'])
def filter_thread(forum_id, thread_id):
    query = "SELECT author, message, timestamp FROM posts WHERE forum_id=%s AND thread_id=%s ORDER BY strftime(timestamp);" % (forum_id, thread_id)
    shard_num = get_shard_num(thread_id)
    app.logger.info(shard_num)
    thread = query_shard_db(query, shard_num)
    if not thread:
        raise InvalidUsage('HTTP 404 Not Found', status_code=404)
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
        guid = uuid.uuid4()
        timestamp = getTimestamp()
        text = reqJSON.get('text').replace("'", "''")
        author = app.config['username']
        data = (guid, forum_id, thread_id, author, timestamp, text)
        shard_name = get_db_name(thread_id)
        app.logger.info(shard_name)

        conn = get_db(shard_name, sqlite3.PARSE_DECLTYPES)
        conn = sqlite3.connect(shard_name, detect_types = sqlite3.PARSE_DECLTYPES)
        conn.text_factory = str
        conn.row_factory = dict_factory
        c = conn.cursor()
        c.execute('INSERT INTO posts VALUES(?,?,?,?,?,?);', data)
        conn.commit()

        query_db("UPDATE threads SET timestamp = '%s' WHERE thread_id='%s';" % (timestamp, thread_id))
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

## Query helper functions
def existsInDB(query):
    result = query_db(query)
    return result[0].values()[0]

def getLatestID():
    id = query_db("SELECT last_insert_rowid()")
    return id[0].values()[0]

def getTimestamp():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")

def get_db_name(thread_id):
    shard_num = int(thread_id) % 3
    if shard_num == 0:
        return SHARD1
    elif shard_num == 1:
        return SHARD2
    else:
        return SHARD3

def get_shard_num(thread_id):
    shard_num = int(thread_id) % 3
    return shard_num

## Database helper functions
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db(db_name, detect_types=0):
    db = getattr(Flask, '_database', None)
    if db is None:
        db = Flask._database = sqlite3.connect(db_name, detect_types=detect_types)
        db.row_factory = dict_factory
    return db


def init():
    with app.app_context():
        db_names = [DATABASE, SHARD1, SHARD2, SHARD3]
        app.logger.info("hello")


        for db_name in db_names:
            if db_name == DATABASE: #rest of tables
                print("rest of db")
                db = get_db(db_name)
                with app.open_resource('init.sql', mode='r') as f:
                    db.cursor().executescript(f.read())
                db.commit()
            else:
                print("shard: " + db_name)
                sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
                sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

                db = get_db(db_name)
                conn = sqlite3.connect(db_name, detect_types = sqlite3.PARSE_DECLTYPES)

                c = conn.cursor()

                if sys.version_info[0] < 3:
                    conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

                c.execute('drop table if exists posts')
                c.execute('CREATE TABLE posts(guid GUID PRIMARY KEY, forum_id INTEGER, thread_id INTEGER, author TEXT, timestamp TEXT, message TEXT)')

                guid = uuid.uuid4()
                print(guid)
                forum_id = 1
                thread_id = 1
                author = 'sam'
                timestamp = 'today'
                message = 'this is some good test data'
                data = (guid, forum_id, thread_id, author, timestamp, message)
                c.execute('INSERT INTO posts VALUES(?,?,?,?,?,?);', data)
                conn.commit()
                c.execute('SELECT * FROM posts')
                print 'Result Data:', c.fetchall()

                conn.commit()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_db(query):
    conn = get_db(DATABASE)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    result = cur.execute(query).fetchall()
    conn.commit()
    return result


def query_shard_db(query, shard_num):
    sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
    sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

    if shard_num == 0:
        db = get_db(SHARD1)
        conn = sqlite3.connect(SHARD1, detect_types = sqlite3.PARSE_DECLTYPES)
    elif shard_num == 1:
        db = get_db(SHARD2)
        conn = sqlite3.connect(SHARD2, detect_types = sqlite3.PARSE_DECLTYPES)
    else:
        db = get_db(SHARD3)
        conn = sqlite3.connect(SHARD3, detect_types = sqlite3.PARSE_DECLTYPES)

    conn.row_factory = dict_factory
    c = conn.cursor()
    app.logger.info(query)
    c.execute(query)
    result = c.fetchall()
    conn.commit()
    return result

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
        for idx, value in enumerate(row))

## exception handler from http://flask.pocoo.org/docs/0.12/patterns/apierrors/
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

## Custom CLI command
@app.cli.command()
def init_db():
    init()

## Run app
if __name__ == "__main__":
    app.run()
