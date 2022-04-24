import os

from flask import Flask, render_template, jsonify
from flask_restful import Api, Resource, abort, reqparse
from flasgger import Swagger, swag_from

steam_web_api_key = "71C62A93E943CF496209037648DA088D"
secret_key = os.urandom(16).hex()

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["DEBUG"] = 1
app.config['SWAGGER'] = {
    'title': 'Flasgger RESTful',
    # 'uiversion': 2,
    'specs_route': '/swagger/'
}

api = Api(app)
swagger = Swagger(app)


@app.route('/api/<string:language>/', methods=['GET'])
@swag_from('test.yml')
def test(language):
    return jsonify(language=language)


@app.route('/', methods=['GET'])
# @swag_from('test.yml')
def index():
    return render_template('index.html', secret_key=app.secret_key)


@app.route('/catalog', methods=['GET'])
# @swag_from('test.yml')
def catalog():
    return render_template('catalog.html', secret_key=app.secret_key)


@app.route('/game-page', methods=['GET'])
# @swag_from('test.yml')
def game_page():
    return render_template('game-page.html', secret_key=app.secret_key)


@app.route('/helper', methods=['GET'])
# @swag_from('test.yml')
def helper():
    return render_template('helper.html', secret_key=app.secret_key)


@app.route('/profile', methods=['GET'])
# @swag_from('test.yml')
def profile():
    return render_template('profile.html', secret_key=app.secret_key)


@app.route('/authors', methods=['GET'])
# @swag_from('test.yml')
def authors():
    return render_template('authors.html', secret_key=app.secret_key)


@app.route('/login', methods=['GET'])
# @swag_from('test.yml')
def login():
    return render_template('login.html', secret_key=app.secret_key)


@app.route('/registrate', methods=['GET'])
# @swag_from('test.yml')
def registrate():
    return render_template('registration.html', secret_key=app.secret_key)


@app.route('/pass-change', methods=['GET'])
# @swag_from('test.yml')
def pass_change():
    return render_template('pass-change.html', secret_key=app.secret_key)


if __name__ == '__main__':
    app.run()
