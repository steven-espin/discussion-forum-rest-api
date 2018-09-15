import flask, sqlite3, click
from flask import Flask, request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum.db'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/', methods=['GET'])
def home():
    return "<h1>Discussion Forum API</h1><p>This site is a prototype API for a discussion forum.</p>"

@app.route('/forums', methods=['GET'])
def forums():
    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_forums = cur.execute('SELECT * FROM forums;').fetchall()
    return jsonify(all_forums)

## Set up CLI command to initialize db according to init.sql schema file
def get_db():
    db = getattr(Flask, '_database', None)
    if db is None:
        db = Flask._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(Flask, '_database', None)
    if db is not None:
        db.close()

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
