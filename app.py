import flask, sqlite3, click
from flask import Flask

app = flask.Flask(__name__)
app.config["DEBUG"] = True
DATABASE = 'forum.db'

@app.route('/', methods=['GET'])
def home():
    return "<h1>Discussion Forum API</h1><p>This site is a prototype API for a discussion forum.</p>"


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
