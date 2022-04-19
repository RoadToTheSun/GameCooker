import os

from flask import Flask, render_template
from flask_restful import Api, Resource, abort, reqparse
from flasgger import Swagger, swag_from

steam_web_api_key = "8FED34B3FCFF02245CD082B65BE01547"
secret_key = os.urandom(16).hex()

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["DEBUG"] = 1
app.config['SWAGGER'] = {'title': 'Flasgger RESTful', 'uiversion': 2}

api = Api(app)
swagger = Swagger(app)
# @app.route('/')
# def hello_world():  # put application's code here
#     return 'Hello World!'


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', secret_key=app.secret_key)


if __name__ == '__main__':
    app.run(debug=True)
