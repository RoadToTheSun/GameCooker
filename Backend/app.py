import os
import json, requests

import steam.webapi
from steam import steamid, webauth, webapi

import logging
from steam.steamid import SteamID
from steam.webapi import WebAPI, WebAPIInterface, WebAPIMethod
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify
from flask_restful import Api, Resource, abort, reqparse
from flasgger import Swagger, swag_from

steam_web_api_key: str
with open("C:/STUDYING/VI/Технологии программирования/steam_key.txt") as path:
    steam_web_api_key = path.read()
steam_id = SteamID(76561198080385483)
secret_key = os.urandom(16).hex()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["DEBUG"] = 1
app.config['SWAGGER'] = {
    'title': 'Flasgger RESTful',
    # 'uiversion': 2,
    'specs_route': '/swagger/'
}

steam_api = WebAPI(
    steam_web_api_key,
    # format="vdf",
)
api = Api(app)
swagger = Swagger(app)


@app.route('/api/<string:language>/', methods=['GET'])
@swag_from('test.yml')
def test(language):
    return jsonify(language=language)


def request_steam_web_api(interface, method, base_url="https://api.steampowered.com", *version, **parameters) -> dict:
    """How to Make a Steam Web API Request:

    Request URL format:

    ``https://{base_url}/{interface}/{method}/{version}?{parameters}``

    :param base_url: Usually ``https://api.steampowered.com``
    :param interface: Indicates which method group (interface) you want to use
    :param method: Indicates which method within the interface you want to use
    :param version: Indicates which version of the method you want to use
    :param parameters: :optional: Parameters are delimited by the & character
    :return: Python dictionary object of response
    """
    response = requests.get(f"https://{base_url}/{interface}/{method}/{version}", parameters)
    response_dict = json.loads(response.text)
    return response_dict


@app.route('/apilist')
def getSupportedAPIList():
    response = steam_api.call('ISteamWebAPIUtil.GetSupportedAPIList')
    return jsonify(response)


@app.route('/', methods=['GET'])
# @swag_from('home.yml')
def index():
    return render_template('index.html', secret_key=app.secret_key)


@app.route('/catalog', methods=['GET'])
# @swag_from('catalog.yml')
def catalog():
    apps = [240, 440, 570, 620, 730]
    page_format = "json"
    # page = f"https://api.steampowered.com/ISteamApps/GetAppList/v2/?key={steam_web_api_key}&format={page_format}"
    # soup = BeautifulSoup(requests.get(page).text, features="html.parser")
    # games = json.loads(soup.text)['applist']['apps']
    response = steam_api.call("ISteamApps.GetAppList", format=page_format)
    games = response['applist']['apps']
    games = [games[_index] for _index in range(len(games)) if games[_index]["name"]
             and (games[_index]["appid"] in apps)
    ]
    # games = json.dumps()
    return render_template('catalog.html', games=games, secret_key=app.secret_key)


@app.route('/game/<int:appid>&<string:appname>', methods=['GET'])
# @swag_from('game.yml')
def game_page(appid, appname):
    page = f"https://store.steampowered.com/api/appdetails/?appids={appid}"
    soup = BeautifulSoup(requests.get(page).text, features="html.parser")
    # print(soup.find("movies").getText('\n'))
    print(page)
    print(soup.text)
    game_data = json.loads(soup.text)[appid]['data']
    return render_template('game-page.html', appid=appid, appname=game_data['name'], secret_key=app.secret_key)


@app.route('/helper', methods=['GET'])
# @swag_from('test.yml')
def helper():
    return render_template('helper.html', secret_key=app.secret_key)


@app.route('/profile', methods=['GET'])
# @swag_from('test.yml')
def profile():
    # user = get_user_from_db(id)
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
