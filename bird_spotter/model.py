import mysql.connector
import flask
import bird_spotter


def get_db():
    """Open a new database connection.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    if 'sqlite_db' not in flask.g:
        flask.g.db = mysql.connector.connect(
            host="localhost",
            user="zhouzhanwang",
            password="password",
            database="411_Database"
        )
        print("Connected to MySQL database")

    return flask.g.db


@bird_spotter.app.teardown_appcontext
def close_db(error):
    """Close the database at the end of a request.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    assert error or not error  # Needed to avoid superfluous style error
    db = flask.g.pop('db', None)
    if db is not None:
        db.commit()
        db.close()
