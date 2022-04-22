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


# @app.route('/')
# def hello_world():  # put application's code here
#     return 'Hello World!'


@app.route('/', methods=['GET'])
@swag_from('test.yml')
def index():
    return render_template('index.html', secret_key=app.secret_key)


@app.route('/api/<string:language>/', methods=['GET'])
@swag_from('test.yml')
def test(language):
    return jsonify(language=language)


if __name__ == '__main__':
    app.run()
