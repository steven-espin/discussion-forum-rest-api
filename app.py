import flask, sqlite3, click
from flask import Flask, request, jsonify
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum.db'

basic_auth = BasicAuth(app)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/', methods=['GET'])
def home():
    return "<h1>Discussion Forum API</h1><p>This site is a prototype API for a discussion forum.</p>"


## HTTP GET methods
@app.route('/forums', methods=['GET'])
def forums_all():
    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_forums = cur.execute('SELECT * FROM forums;').fetchall()
    return jsonify(all_forums)

@app.route('/forums/<forum_id>', methods=['GET'])
def filter_forum(forum_id):
    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    forum = cur.execute("SELECT thread_id, title, creator, timestamp FROM threads WHERE forum_id=%s;" % forum_id).fetchall()
    return jsonify(forum)

@app.route('/forums/<forum_id>/<thread_id>', methods=['GET'])
def filter_thread(forum_id, thread_id):
    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    thread = cur.execute("SELECT author, text, timestamp FROM posts WHERE forum_id=%s AND thread_id=%s;" % (forum_id, thread_id)).fetchall()
    return jsonify(thread)

## Resource path not valid
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


## Set up CLI command to initialize db according to init.sql schema file
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

@app.cli.command()
def init_db():
    init()


if __name__ == "__main__":
    app.run()
