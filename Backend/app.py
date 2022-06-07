import locale
import os
from os import path
import json, requests
from datetime import datetime

import sqlalchemy.orm
from jinja2 import Environment
from sqlalchemy import func
from sqlalchemy.orm import Query
from flask_sqlalchemy import SQLAlchemy, Pagination

import steam.webapi
# import jwt
from flask_login import login_required, logout_user, current_user, login_user, LoginManager, login_manager
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
from flask_security.utils import hash_password

parent_dir = path.dirname(path.abspath(__file__))
steam_web_api_key: str
with open(path.join(parent_dir, 'steam_key.txt')) as file:
    steam_web_api_key = file.read()
# with open(path.join(app.root_path, 'steam_key.txt')) as file:
#     steam_web_api_key = file.read()
steam_id = SteamID(76561198273560595)

app = Flask(__name__, template_folder='templates')
app.config["DEBUG"] = 1
app.config["APPLICATION_ROOT"] = app.root_path
app.config['SWAGGER'] = {
    # 'title': 'GameCooker API',
    # 'doc_dir': './restapi/swagger/',
    'uiversion': 3,
    'doc_dir': f'{path.join(app.root_path, "restapi", "swagger")}',
    # 'endpoint': 'swagger',
    # 'route': '/swagger'
}
print(app.config)
app.secret_key = os.urandom(16).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameCooker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login123.html'

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'swagger',
            "route": '/restapi',
            # "rule_filter": lambda rule: True,  # all in
            # "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "/restapi/swagger",  # must be set by user
    "specs_route": "/swagger"
}

migrate = Migrate(app, db)

# restapi = Api()
db.init_app(app)
logging.basicConfig(level=logging.DEBUG)

steam_api = WebAPI(
    steam_web_api_key,
    # format="vdf",
)
# from restapi.steam import api_steam
from restapi import steam_API, main

app.register_blueprint(main.api_main, url_prefix='/main-api')
app.register_blueprint(steam_API.api_steam, url_prefix='/steam-api')

swagger = Swagger(
    app,
    template_file=os.path.join(app.root_path, 'restapi', 'swagger', 'swagger.yaml'),
    parse=True,
    config=swagger_config
)
# print(swagger.template_file)
# print(f"URL_MAP: {app.url_map}")


class AdminMixin:
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.has_role('admin')
        return

    def inaccessible_callback(self, name, **kwargs):
        # localhost/admin -> login
        return redirect(url_for('login123', next=request.url))


class AdminView(AdminMixin, ModelView):
    pass


class HomeAdminView(AdminMixin, AdminIndexView):
    pass

# db.create_all()


# Admin
admin = Admin(app, 'GameCooker', url='/login123', index_view=HomeAdminView(name='Home'))
admin.add_view(AdminView(User, db.session))
admin.add_view(AdminView(Role, db.session))
admin.add_view(AdminView(Game, db.session))
admin.add_view(AdminView(Genre, db.session))
# Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

manager = LoginManager(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login123'
login_manager.login_message = 'Войдите, чтобы попасть на эту страницу'


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


def unauthorized_handler() -> Response:
    return redirect(url_for("login123"))


@app.before_first_request
def create_tables():
    db.create_all()
    # user_datastore.create_user(email='matt@nobien.net', password='password')
    # db.session.commit()


@app.route('/', methods=['GET'])
# @swag_from('home.yml')
def index():
    return render_template('index.html', secret_key=app.secret_key)


# @swag_from("catalog.yaml")
@app.route('/catalog', methods=['GET'])
# @swag_from('catalog.yml')
def catalog():
    GAMES_PER_PAGE = 8
    GAMES_PER_PAGE_MAX = 24
    page = request.args.get('page', 1, int)
    games: Pagination = Game.query.paginate(page=page, error_out=True, per_page=GAMES_PER_PAGE, max_per_page=GAMES_PER_PAGE_MAX)
    # json_games = requests.get(url_for("main-restapi.catalog", page=page, _external=True)).json()
    # games_dict: Dict[dict] = json_games["games"]
    # logging.info(games_dict)

    return render_template('catalog.html', games=games, secret_key=app.secret_key)


# @swag_from("catalog.yaml", methods="GET")
@app.route('/game/<int:app_id>', methods=['GET'])
# @swag_from('game.yml')
def game_page(app_id, key=steam_web_api_key, l="russian"):
    _game_data = requests.get(url_for("steam-restapi.get_app_info", app_id=app_id, key=key, l=l, _external=True)).text
    game_data_dict = json.loads(_game_data)
    # logging.info("Movies: \n" + json.dumps(game_data_dict, indent=2))
    logging.info(game_data_dict)
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


# @swag_from("helper.yaml")
@app.route('/helper', methods=['GET', 'POST'])
@login_required
# @swag_from('helper.yml')
def helper():
    all_genres = Genre.query.all()
    if request.method == "GET":
        genres_of_games = request.args.getlist('genres')
        genres_of_games.sort()
        gamers = request.args.get('gamers')
        cost = request.args.get('cost')
        all_games = Game.query.all()
        max_players = db.session.query(func.max(Game.players_count)).one()[0]
        games = []
        for game in all_games:
            temp_list = []
            checker = False
            for el in game.genres:
                temp_list.append(el.id)
            if len(genres_of_games) == len(temp_list):
                for i in range(len(genres_of_games)):
                    if int(genres_of_games[i]) == temp_list[i]:
                        checker = True
            if checker and int(gamers) <= game.players_count and int(cost) == game.price:
                games.append(game)
        return render_template('helper.html', genres=all_genres, games=games, max_players=max_players)

    return render_template('helper.html', genres=all_genres)


@app.route('/profile', methods=['GET'])
@login_required
# @swag_from('profile.yaml')
def profile():
    # user = get_user_from_db(id)
    return render_template('profile.html', secret_key=app.secret_key)


@app.route('/authors', methods=['GET'])
# @swag_from('authors.yml')
def authors():
    return render_template('authors.html', secret_key=app.secret_key)


# @swag_from("login.yaml", methods=["GET", "POST"])
@app.route('/login123', methods=['GET', 'POST'])
# @swag_from('login.yml')
def login123():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    if request.method == "POST":
        email = request.form['login-mail']
        password = request.form['password']
        user = User.query.filter_by(login_mail=email).first()
        if not user or not check_password_hash(user.pass_hash, password):
            flash('Please check your login details and try again.')
        login_user(user)
        return redirect(url_for('profile'))
    # if the above check passes, then we know the user has the right credentials
    return render_template('login123.html', secret_key=app.secret_key)


# @swag_from("post.yaml")
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
                flash("Успешно зарегистрировались")
            except:
                return "Ошибка, проверьте введенные данные"
            return redirect(url_for('login123'))
        else:
            flash("Неверно заполнены поля")
    return render_template('registration.html')


# @swag_from("pass_change.yaml")
@app.route('/pass-change', methods=['GET', 'POST'])
@login_required
# @swag_from('pass-change.yml')
def pass_change():
    # should be --PUT--
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


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')


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


@app.context_processor
def slice_text():
    import textwrap
    def short_text(_text, _width=80, _placeholder='...'):
        return textwrap.shorten(text=_text, width=_width, placeholder=_placeholder)
    return dict(short=short_text)


@app.template_filter('reverse')
def reverse_filter(s):
    return s[::-1]


if __name__ == '__main__':
    jinja_env = Environment(extensions=['jinja2.ext.loopcontrols'])
    app.run(debug=True)
