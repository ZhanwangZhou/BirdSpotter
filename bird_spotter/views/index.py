"""
Bird Spotter index (main) view.

URLs include:
/
"""
import flask
import bird_spotter
from flask import request, redirect, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import uuid
import os


@bird_spotter.app.route('/')
def show_index():
    """Display / route."""
    return flask.render_template("index.html")


@bird_spotter.app.route('/api/search', methods=['GET'])
def search():
    text = flask.request.args.get('text', default='abc', type=str)
    connection = bird_spotter.model.get_db()
    print(text)
    if text == 'default':
        response = bird_spotter.model.get_random_birds(10, connection)
        response = {
            'status': 'success',
            'data': response
        }
        print(response)
        return flask.jsonify(response), 200
    response = bird_spotter.model.get_bird_by_sci_name(text, connection)
    if response == {}:
        response = bird_spotter.model.get_bird_by_com_name(text, connection)
    if response == {}:
        return flask.jsonify({'status': 'error', 'message': 'Not Found'}), 404
    response = {
        'status': 'success',
        'data': [response]
    }
    return flask.jsonify(response), 200


@bird_spotter.app.route('/api/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    image_folder = flask.current_app.config["UPLOAD_FOLDER"]
    allowed_exts = flask.current_app.config.get("ALLOWED_EXTENSIONS", ['.jpg'])
    
    for ext in allowed_exts:
        filename = f"{image_id}{ext}"
        file_path = os.path.join(image_folder, filename)
        if os.path.exists(file_path):
            return send_from_directory(image_folder, filename)
    
    return jsonify({"message": "Image not found"}), 404


@bird_spotter.app.route('/api/events', methods=['GET'])
def get_events():
    connection = bird_spotter.model.get_db()
    cursor = connection.cursor()

    search = flask.request.args.get('search', default=None, type=str)

    base_query = """
        SELECT 
            E.event_id,
            E.user_id,
            E.event_time,
            E.longitude,
            E.latitude,
            E.Country,
            E.State,
            B.bird_common_name,
            B.bird_scientific_name,
            I.image_id
        FROM Event E
        JOIN Bird B ON E.bird_scientific_name = B.bird_scientific_name
        LEFT JOIN Image I ON E.event_id = I.event_id
    """

    if search:
        base_query += " WHERE B.bird_scientific_name LIKE %s"
        cursor.execute(base_query, (f'%{search}%',))
    else:
        return "bird name not provided", 500

    results = cursor.fetchall()
    events = []
    for row in results:
        image_id = row[9]
        image_url = f"/api/images/{image_id}" if image_id else ""

        events.append({
            "event_id": row[0],
            "user_id": row[1],
            "event_time": row[2].isoformat(),
            "longitude": float(row[3]),
            "latitude": float(row[4]),
            "Country": row[5],
            "State": row[6],
            "bird_name": row[7],
            "bird_scientific_name": row[8],
            "image_url": image_url
        })

    cursor.close()
    return flask.jsonify({"status": "success", "data": events}), 200


@bird_spotter.app.route('/api/events/page', methods=['GET'])
def get_events_paginated():
    connection = bird_spotter.model.get_db()
    cursor = connection.cursor()

    page = flask.request.args.get('page', default=1, type=int)
    page=max(page,1)
    limit = flask.request.args.get('limit', default=10, type=int)
    sort = flask.request.args.get('sort', default="event_time:desc", type=str)

    offset = (page - 1) * limit

    main_query = f"""
        SELECT 
            E.event_id,
            E.user_id,
            E.event_time,
            E.longitude,
            E.latitude,
            E.Country,
            E.State,
            B.bird_common_name,
            B.bird_scientific_name,
            I.image_id
        FROM Event E
        JOIN Bird B ON E.bird_scientific_name = B.bird_scientific_name
        LEFT JOIN Image I ON E.event_id = I.event_id
        ORDER BY E.event_time DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(main_query, (limit, offset))
    results = cursor.fetchall()

    events = []
    for row in results:
        image_id = row[9]
        image_url = f"/api/images/{image_id}" if image_id else ""
        events.append({
            "event_id": row[0],
            "user_id": row[1],
            "event_time": row[2].isoformat(),
            "longitude": float(row[3]),
            "latitude": float(row[4]),
            "country": row[5],
            "state": row[6],
            "bird_name": row[7],
            "bird_scientific_name": row[8],
            "image_url": image_url
        })

    cursor.execute("SELECT COUNT(*) FROM Event")
    total_items = cursor.fetchone()[0]
    total_pages = (total_items + limit - 1) // limit

    cursor.close()

    return flask.jsonify({
        "status": "success",
        "data": {
            "events": events,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "has_next": page < total_pages
            }
        }
    }), 200


@bird_spotter.app.route("/api/upload", methods=["POST"])
def upload_bird_sighting():
    connection = bird_spotter.model.get_db()

    bird_name = flask.request.form.get('bird_scientific_name')
    latitude = flask.request.form.get('latitude')
    longitude = flask.request.form.get('longitude')
    country = flask.request.form.get('country')
    state = flask.request.form.get('state')

    user_id = flask.request.form.get('user_id')
    if not user_id:
        user_id = 1  # Default user_id for testing

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
