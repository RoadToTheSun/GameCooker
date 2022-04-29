import locale
import os
import json, requests
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

import steam.webapi
# import jwt
from flask_login import login_required, logout_user, current_user, login_user, LoginManager
from requests import Response
from steam import steamid, webauth, webapi

import logging
from steam.steamid import SteamID
from steam.webapi import WebAPI, WebAPIInterface, WebAPIMethod
from flask import Flask, render_template, jsonify, Markup, flash, redirect, url_for, request, make_response
from flask_restful import Api, Resource, abort, reqparse
from flasgger import Swagger, swag_from
from typing import List

from werkzeug.exceptions import NotFound, Forbidden, BadRequest, NotImplemented
from werkzeug.security import check_password_hash, generate_password_hash

from Backend.user import User

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

manager = LoginManager(app)
manager.session_protection = "strong"
manager.login_view = "index"
manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
manager.login_message_category = "success"


def unauthorized_handler() -> Response:
    return redirect(url_for("login"))


@manager.user_loader
def load_user(user_id):
    return User(None).from_db(None, user_id)


steam_api = WebAPI(
    steam_web_api_key,
    # format="vdf",
)
api = Api(app)
swagger = Swagger(app)
# db = SQLAlchemy(app)

@app.route('/api/<string:language>/', methods=['GET'])
@swag_from('test.yml')
def test(language):
    return jsonify(language=language)


def request_steam_web_api(interface, method, base_url="api.steampowered.com", version="v001",
                          parameters: dict = None) -> dict:
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

    # Already available from webapi module
    # response = webapi.webapi_request(f"https://{base_url}/{interface}/{GET}/{version}", 'GET', params=parameters)
    if not parameters:
        parameters = {'format': 'json'}
    response = requests.get(f"https://{base_url}/{interface}/{method}/{version}", parameters)
    response_dict = json.loads(response.text)
    return response_dict


@app.route('/apilist')
def getSupportedAPIList():
    response = steam_api.call('ISteamWebAPIUtil.GetSupportedAPIList')
    interfaces: list = steam_api.interfaces
    logging.info(', '.join([str(i.doc()) for i in interfaces]))
    # logging.info([[method.name for method in interface.__iter__()] for interface in interfaces])
    # response = request_steam_web_api("ISteamWebAPIUtil", "GetSupportedAPIList")
    return jsonify(response)


@app.route('/apps', methods=['GET'])
# @swag_from('apps.yml')
def getAppsFromStoreService():
    response = steam_api.call('IStoreService.GetAppList')
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


@app.route('/game/<int:appid>', methods=['GET'])
# @swag_from('game.yml')
def game_page(appid):
    url = f"https://store.steampowered.com/api/appdetails/?appids={appid}&key={steam_web_api_key}&l=russian"
    response: dict = webapi.webapi_request(url)
    game_data_dict = response[f'{appid}']['data']
    logging.info("Movies: \n" + json.dumps(game_data_dict, indent=2))
    game_screenshots = game_data_dict['screenshots']
    game_trailers = game_data_dict['movies']
    sd = Markup(game_data_dict['short_description'])
    dd = Markup(game_data_dict['detailed_description'])
    # from boltons import strutils
    # sd = strutils.html2text(game_data_dict['short_description'])
    # dd = strutils.html2text(game_data_dict['detailed_description'])
    # return json.dumps(game_data_dict, skipkeys=True, ensure_ascii=False)
    return make_response(render_template('game-page.html', game=game_data_dict, sd=sd, dd=dd))


@app.route('/helper', methods=['GET', 'POST'])
# @swag_from('helper.yml')
def helper():
    return render_template('helper.html', secret_key=app.secret_key)


@app.route('/profile', methods=['GET'])
# @swag_from('profile.yml')
def profile():
    # user = get_user_from_db(id)
    return render_template('profile.html', secret_key=app.secret_key)


@app.route('/authors', methods=['GET'])
# @swag_from('authors.yml')
def authors():
    return render_template('authors.html', secret_key=app.secret_key)


@app.route('/login', methods=['GET', 'POST'])
# @swag_from('login.yml')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    # if request.method == "POST":
    #     rm = True if request.form.get('remember-me') else False
    #     user = db.get_user_by_login(request.form['login-mail'])
    #     if user and (check_password_hash(user['pass_hash'], request.form['pass'])):
    #         user_obj = User(user)
    #         login_user(user_obj, remember=rm)
    #         flash(f'Successfully logged in as {user_obj.get_login()} ' +
    #               ('(admin)' if user_obj.get_role() == 1 else
    #                '(user)'))
    #         flash(f'Ur hashed password is {user_obj.get_hash()}', "success")
    #         return redirect(request.args.get('next') or url_for("profile"))
    #     error = 'Неверная пара логин/пароль'
    #     flash(error, "error")
    return render_template('login.html', secret_key=app.secret_key)


@app.route('/registrate', methods=['GET', 'POST'])
# @swag_from('registrate.yml')
def registrate():
    import validators
    error = None
    # if request.method == "POST":
    #     if validators.email(request.form['login-mail']) \
    #             and request.form['pass'] == request.form['pass2']:
    #         # TODO add check if user exists
    #         # and:
    #         rm = True if request.form.get('remember-me') else False
    #         pass_hash = generate_password_hash(request.form['pass'])
    #         role = 1 if 'admin' in request.form['pass'] else 0
    #         res = db.add_user(request.form['nickname'], request.form['login-mail'], pass_hash, role)
    #         if res:
    #             flash("Вы успешно зарегистрированы", "success")
    #             user = db.get_user_by_login(request.form['login-mail'])
    #             user_obj = User(user)
    #             login_user(user_obj, remember=rm)
    #             flash(f'Ur hashed_password is {user_obj.get_hash()}', "success")
    #             return redirect(url_for('profile', id=user_obj['id']))
    #         error = 'Ошибка при добавлении в БД'
    #         flash(error, "error")

    return render_template('registration.html', secret_key=app.secret_key)


@app.route('/pass-change', methods=['GET'])
# @swag_from('pass-change.yml')
def pass_change():
    return render_template('pass-change.html', secret_key=app.secret_key)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    # return redirect(url_for('index'))
    pass


@app.after_request
def add_header(response):
    # response.cache_control.max_age = 1
    return response


@app.errorhandler(NotFound)
def not_found(error):
    flash(error, 'error')
    code = NotFound.code
    message = "Такой страницы не существует"
    return render_template('error-handler.html', response=dict({code:message})), 404


@app.errorhandler(NotImplemented)
def not_implemented(error):
    flash(error, 'error')
    code = NotImplemented.code
    message = "Такой страницы не существует"
    return render_template('error-handler.html', response=dict({code:message})), 501


@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)


if __name__ == '__main__':
    app.run(debug=True)
