import flask, sqlite3, click, logging, json
from flask import Flask, request, jsonify
from flask_basicauth import BasicAuth


app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum.db'

class dbAuth(BasicAuth):
    def check_credentials(this, username, password):
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
    forum = query_db("SELECT thread_id, title, creator, timestamp FROM threads WHERE forum_id=%s;" % forum_id)
    return jsonify(forum)

@app.route('/forums/<forum_id>/<thread_id>', methods=['GET'])
def filter_thread(forum_id, thread_id):
    thread = query_db("SELECT author, text, timestamp FROM posts WHERE forum_id=%s AND thread_id=%s;" % (forum_id, thread_id))
    return jsonify(thread)

## HTTP POST methods

## HTTP PUT methods
@app.route('/users/<username>', methods = ['PUT'])
@basicAuth.required
def change_password(username):
    return "putting %s" % username


## Resource path not valid
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


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
    return result


## Custom CLI command
@app.cli.command()
def init_db():
    init()


if __name__ == "__main__":
    app.run()
