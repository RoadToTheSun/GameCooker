import locale
import os
from os import path
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
from flask_migrate import Migrate
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore, Security
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
# from Backend.user import User

parent_dir = path.dirname(path.abspath(__file__))
steam_web_api_key: str
with open(path.join(parent_dir, 'steam_key.txt')) as file:
    steam_web_api_key = file.read()
steam_id = SteamID(76561198273560595)

app = Flask(__name__)
app.config["DEBUG"] = 1
app.config['SWAGGER'] = {
    'title': 'Flasgger RESTful',
    # 'uiversion': 2,
    'specs_route': '/swagger/'
}
app.secret_key = 'very very secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameCooker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

db = SQLAlchemy(app)

manager = LoginManager(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.DEBUG)


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )

user_games = db.Table('user_games',
                      db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                      db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                      db.Column('user_rating', db.Boolean()),
                      db.Column('favourite', db.Integer())
                      )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100))
    login_mail = db.Column(db.String(100), unique=True)
    pass_hash = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    users_rating = db.relationship('Game', secondary=user_games, backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(100))


game_genres = db.Table('game_genres',
                       db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                       db.Column('genre_id', db.Integer(), db.ForeignKey('genre.id'))
                       )


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    players_count = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    genres = db.relationship('Genre', secondary=game_genres, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return self.name


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class AdminMixin:
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        # localhost/admin -> login
        return redirect(url_for('security.login', next=request.url))


class AdminView(AdminMixin, ModelView):
    pass


class HomeAdminView(AdminMixin, AdminIndexView):
    pass


# Admin
admin = Admin(app, 'Game-Cooker', url='/login', index_view=HomeAdminView(name='Home'))
admin.add_view(AdminView(User, db.session))
admin.add_view(AdminView(Role, db.session))
admin.add_view(AdminView(Game, db.session))
admin.add_view(AdminView(Genre, db.session))
# Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
# security = Security(app, user_datastore)

manager = LoginManager(app)
manager.session_protection = "strong"
manager.login_view = "index"
manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
manager.login_message_category = "success"


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def unauthorized_handler() -> Response:
    return redirect(url_for("login"))


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
    #  import validators
    # error = None
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
