"""REST API for posts."""
import flask
from flask import session, request
import bird_spotter


@bird_spotter.app.route('/api/v1/', methods=['GET'])
def get_services():
    """Show services."""
    response = {
        'comments': '/api/v1/comments/',
        'events': '/api/v1/events/',
        'url': '/api/v1/'
    }
    return flask.jsonify(response), 200
