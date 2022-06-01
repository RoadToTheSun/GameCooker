import locale
import os
from os import path
import json, requests
from datetime import datetime

import sqlalchemy.orm
from sqlalchemy.orm import Query
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
from data_base.models import *
# from Backend.user import User
from flask_security.utils import encrypt_password, hash_password

parent_dir = path.dirname(path.abspath(__file__))
steam_web_api_key: str
with open(path.join(parent_dir, 'steam_key.txt')) as file:
    steam_web_api_key = file.read()
# with open(path.join(app.root_path, 'steam_key.txt')) as file:
#     steam_web_api_key = file.read()
steam_id = SteamID(76561198273560595)

app = Flask(__name__, template_folder='templates')
app.config["DEBUG"] = 1
app.config['SWAGGER'] = {
    'title': 'GameCooker API',
    'uiversion': 3,
    'specs_route': '/swagger/',
    # 'doc_dir': f'{path.join(app.root_path, "swagger")}',
    # 'endpoint': 'api',
    # 'route': '/api'
}
app.secret_key = os.urandom(16).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameCooker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'security/login123.html'

db = SQLAlchemy(app)

manager = LoginManager(app)
migrate = Migrate(app, db)

steam_api = WebAPI(
    steam_web_api_key,
    # format="vdf",
)
api = Api(app)
swagger = Swagger(app)

logging.basicConfig(level=logging.DEBUG)


class AdminMixin:
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        # localhost/admin -> login
        return redirect(url_for('login123', next=request.url))


class AdminView(AdminMixin, ModelView):
    pass


class HomeAdminView(AdminMixin, AdminIndexView):
    pass

# db.create_all()

# Admin
admin = Admin(app, 'Game-Cooker', url='/login123', index_view=HomeAdminView(name='Home'))
admin.add_view(AdminView(User, db.session))
admin.add_view(AdminView(Role, db.session))
admin.add_view(AdminView(Game, db.session))
admin.add_view(AdminView(Genre, db.session))
# Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

manager = LoginManager(app)
manager.session_protection = "strong"
manager.login_view = "index"
manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
manager.login_message_category = "success"


@app.before_first_request
def addSteamGames():
    import random, csv
    deleted_rows = Game.query.delete()
    logging.warning(f"{deleted_rows} ROWS WERE DELETED FROM `GAME`")
    games: List[Game] = []
    ids = []
    with open(path.join(app.root_path, 'resources', 'games.csv'), 'r') as game_ids:
        for _id in csv.reader(game_ids):
            ids.append(int(_id[0]))
    logging.info('GAME IDS TO BE ADDED: '+', '.join(map(str, ids)))
    for _id in ids:
        url = f"https://store.steampowered.com/api/appdetails/?appids={_id}&key={steam_web_api_key}&l=russian"
        response: dict = webapi.webapi_request(url)
        game_info = response[f'{_id}']['data']
        name: str = game_info['name']
        players_count: int = random.randint(1, 10)
        price: int = random.randint(0, 1)
        # rating = None
        preview_url: str = f"https://steamcdn-a.akamaihd.net/steam/apps/{_id}/header.jpg"
        game = Game(id=_id, name=name, players_count=players_count, price=price, preview_url=preview_url)
        games.append(game)
    try:
        db.session.add_all(games)
        db.session.commit()
    except Exception as e:
        logging.exception("AN ERROR OCCURRED WHILE ADDING GAME", exc_info=e)
    finally:
        _json: Response = jsonify(Game.query.all())
        logging.info(_json)
        return _json


def unauthorized_handler() -> Response:
    return redirect(url_for("login"))


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def unauthorized_handler() -> Response:
    return redirect(url_for("login123"))

@app.before_first_request
def create_user():
    db.create_all()
    # user_datastore.create_user(email='matt@nobien.net', password='password')
    # db.session.commit()

@app.route('/api/<string:language>/', methods=['GET'])
@swag_from('test.yml')
def test(language):
    return jsonify(language=language)



@swag_from("apilist.yaml")
@app.route('/api/apilist')
def getSupportedAPIList():
    response = steam_api.call('ISteamWebAPIUtil.GetSupportedAPIList')
    interfaces: list = steam_api.interfaces
    logging.info(', '.join([str(i.doc()) for i in interfaces]))
    # logging.info([[method.name for method in interface.__iter__()] for interface in interfaces])
    # response = request_steam_web_api("ISteamWebAPIUtil", "GetSupportedAPIList")
    return jsonify(response)


@swag_from("apps.yaml")
@app.route('/apps', methods=['GET'])
# @swag_from('apps.yml')
def getAppsFromStoreService():
    response = steam_api.call('IStoreService.GetAppList')
    return jsonify(response)


@app.route('/', methods=['GET'])
# @swag_from('home.yml')
def index():
    return render_template('index.html', secret_key=app.secret_key)


@swag_from("catalog.yaml")
@app.route('/catalog', methods=['GET'])
# @swag_from('catalog.yml')
def catalog():
    from sqlalchemy.orm import query
    games: query.Query = Game.query.all()
    page_format = "json"
    # page = f"https://api.steampowered.com/ISteamApps/GetAppList/v2/?key={steam_web_api_key}&format={page_format}"
    # soup = BeautifulSoup(requests.get(page).text, features="html.parser")
    # games = json.loads(soup.text)['applist']['apps']
    # response = steam_api.call("ISteamApps.GetAppList", format=page_format)
    # games = response['applist']['apps']
    # games = [games[_index] for _index in range(len(games)) if games[_index]["name"]
    #          and (games[_index]["appid"] in apps)
    #          ]
    # games = json.dumps()
    return render_template('catalog.html', games=games, secret_key=app.secret_key)


@swag_from("catalog.yaml", methods="GET")
@app.route('/game/<int:appid>', methods=['GET'])
# @swag_from('game.yml')
def game_page(appid):
    url = f"https://store.steampowered.com/api/appdetails/?appids={appid}&key={steam_web_api_key}&l=russian"
    response: dict = webapi.webapi_request(url)
    game_data_dict = response[f'{appid}']['data']
    logging.info("Movies: \n" + json.dumps(game_data_dict, indent=2))
    game_screenshots = game_data_dict['screenshots']
    # game_trailers = game_data_dict['movies']
    sd = Markup(game_data_dict['short_description'])
    dd = Markup(game_data_dict['detailed_description'])
    # If we want just a plain text:
    # from boltons import strutils
    # sd = strutils.html2text(game_data_dict['short_description'])
    # dd = strutils.html2text(game_data_dict['detailed_description'])
    # return json.dumps(game_data_dict, skipkeys=True, ensure_ascii=False)
    return make_response(render_template('game-page.html', game=game_data_dict, sd=sd, dd=dd))


@swag_from("helper.yaml")
@app.route('/helper', methods=['GET', 'POST'])
# @swag_from('helper.yml')
def helper():
    return render_template('helper.html', secret_key=app.secret_key)


@swag_from("profile.yaml")
@app.route('/profile', methods=['GET'])
# @swag_from('profile.yml')
def profile():
    # user = get_user_from_db(id)
    return render_template('profile.html', secret_key=app.secret_key)


@app.route('/authors', methods=['GET'])
# @swag_from('authors.yml')
def authors():
    return render_template('authors.html', secret_key=app.secret_key)


@swag_from("login.yaml", methods=["GET", "POST"])
@app.route('/login', methods=['GET', 'POST'])
# @swag_from('login.yml')
def login123():
    if request.method == "POST":
        email = request.form['login-mail']
        password = request.form['password']
        user = User.query.filter_by(login_mail=email).first()
        if not user or not check_password_hash(user.pass_hash, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('profile'))
        login_user(user)
    # if the above check passes, then we know the user has the right credentials
    return render_template('login123.html', secret_key=app.secret_key)


@swag_from("registrate.yaml")
@app.route('/registrate', methods=['GET', 'POST'])
# @swag_from('registrate.yml')
def registrate():
    if request.method == "POST":
        if request.form['password'] == request.form['password2']:
            user = User(nickname=request.form['nickname'], login_mail=request.form['login-mail'],
                        pass_hash=generate_password_hash(request.form['password']), active=True)
            try:
                db.session.add(user)
                db.session.commit()
            except:
                return "Ошибка, проверьте введенные данные"
            return redirect(url_for('login123'))
        else:
            flash("Неверно заполнены поля")
    return render_template('registration.html')


@swag_from("pass_change.yaml")
@app.route('/pass-change', methods=['PUT'])
# @swag_from('pass-change.yml')
def pass_change():
    if request.method == "POST":
        user = User.query.get(current_user.id)
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        new_password2 = request.form['new_password2']
        if check_password_hash(user.pass_hash, old_password) and \
                new_password == new_password2:
            user.pass_hash = generate_password_hash(new_password)
            db.session.commit()
        else:
            flash("Неверно заполнены поля")
    return render_template('pass-change.html', secret_key=app.secret_key)


@app.route('/logout')
@login_required
def logout():
    return redirect(url_for('security.logout'))


@app.after_request
def add_header(response):
    # response.cache_control.max_age = 1
    return response


# @app.errorhandler(NotFound)
# def not_found(error):
#     flash(error, 'error')
#     code = NotFound.code
#     message = "Такой страницы не существует"
#     return render_template('error-handler.html', response=dict({code:message})), 404
#
#
# @app.errorhandler(NotImplemented)
# def not_implemented(error):
#     flash(error, 'error')
#     code = NotImplemented.code
#     message = "Такой страницы не существует"
#     return render_template('error-handler.html', response=dict({code:message})), 501


@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)


if __name__ == '__main__':
    app.run(debug=True)
