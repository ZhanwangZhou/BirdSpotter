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


def get_random_birds(num, connection):
    cursor = connection.cursor()
    query = """SELECT * FROM Bird
    ORDER BY RAND()
    LIMIT %s
    """
    cursor.execute(query, (num,))
    results = cursor.fetchall()
    results = [
        {"bird_scientific_name": result[0],
         "bird_common_name": result[1],
         "bird_description": result[2]} for result in results
    ]
    cursor.close()
    return results


def get_bird_by_sci_name(bird_sci_name, connection):
    cursor = connection.cursor()
    query = """SELECT * FROM Bird
    WHERE bird_scientific_name = %s"""
    cursor.execute(query, (bird_sci_name,))
    result = cursor.fetchall()
    if len(result) == 0:
        return {}
    result = result[0]
    result = {"bird_scientific_name": result[0],
              "bird_common_name": result[1],
              "bird_description": result[2]}
    cursor.close()
    return result


def get_bird_by_com_name(bird_com_name, connection):
    cursor = connection.cursor()
    query = """SELECT * FROM Bird
    WHERE bird_common_name = %s"""
    cursor.execute(query, (bird_com_name,))
    result = cursor.fetchall()
    if len(result) == 0:
        return {}
    result = result[0]
    result = {"bird_scientific_name": result[0],
              "bird_common_name": result[1],
              "bird_description": result[2]}
    cursor.close()
    return result
