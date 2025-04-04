"""
Bird Spotter index (main) view.

URLs include:
/
"""
import flask
import bird_spotter
from flask import request, redirect


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
