"""
Bird Spotter index (main) view.

URLs include:
/
"""
import flask
import bird_spotter
from flask import request, redirect
from werkzeug.utils import secure_filename
import uuid
import os


@bird_spotter.app.route('/')
def show_index():
    """Display / route."""
    return flask.render_template("index.html")


@bird_spotter.app.route('/search/', methods=['POST'])
def search_bird():
    operation = request.form.get('operation')
    text = request.form.get('text')
    print(operation, text)
    if operation == 'search_by_sci':
        url = '/bird/' + text.replace(' ', '+') + '/'
        print("**********", url)
    else:
        url = '/'
    return redirect(url)


@bird_spotter.app.route('/bird/<bird_sci_name>/')
def bird(bird_sci_name):
    connection = bird_spotter.model.get_db()
    context = bird_spotter.model.get_bird_by_sci_name(bird_sci_name.replace('+', ' '), connection)
    # Corvus brachyrhynchos
    # context = bird_spotter.model.get_birds_by_com_name("American crow", connection)[0]
    context["logname"] = "Anteater"
    return flask.render_template("bird.html", **context)

@bird_spotter.app.route("/api/upload", methods=["POST"])
def upload_bird_sighting():
    connection = bird_spotter.model.get_db()

    bird_name = flask.request.form.get('bird_scientific_name')
    latitude = flask.request.form.get('latitude')
    longitude = flask.request.form.get('longitude')
    country = flask.request.form.get('country')
    state = flask.request.form.get('state')

    user_id = 1 #TODO: get user_id from session or token

    file = flask.request.files.get("file")
    if not file:
        return "No file uploaded", 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in flask.current_app.config["ALLOWED_EXTENSIONS"]:
        return "Unsupported file type", 400


    try:
        cursor = connection.cursor()
        insert_event = """INSERT INTO Event (user_id, event_time, longitude, latitude, Country, State, bird_scientific_name)
                            VALUES (%s, NOW(), %s, %s, %s, %s, %s)"""
        cursor.execute(insert_event, (user_id, longitude, latitude, country, state, bird_name))
        event_id = cursor.lastrowid

        insert_image = """INSERT INTO Image (event_id, bird_scientific_name)
                            VALUES (%s, %s)"""
        cursor.execute(insert_image, (event_id, bird_name))
        image_id = cursor.lastrowid

        filename = secure_filename(f"{image_id}{ext}")
        image_folder = flask.current_app.config["UPLOAD_FOLDER"]
        os.makedirs(image_folder, exist_ok=True)
        image_path = os.path.join(image_folder, filename)
        file.save(image_path)


        connection.commit()
        cursor.close()

        return flask.jsonify({"message": "Upload successful", "image_id": image_id}), 200

    except Exception as e:
        print(e)
        connection.rollback()
        return "Database insert error", 500