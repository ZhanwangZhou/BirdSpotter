"""
Bird Spotter index (main) view.

URLs include:
/
"""
import flask
import bird_spotter


@bird_spotter.app.route('/')
def show_index():
    """Display / route."""
    context = {"bird_name": "sparrow"}
    return flask.render_template("index.html", **context)