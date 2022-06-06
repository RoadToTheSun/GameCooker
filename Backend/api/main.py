import dataclasses
import sqlite3
from os import path

import requests
import sqlalchemy
from flask import Flask, Blueprint, request
from flask_restful import Resource, Api, reqparse
from flask import jsonify
from flask.views import MethodView
import logging
from flasgger import swag_from
# from flask_jwt_extended import jwt_required, get_jwt_identity

from Backend.data_base.models import *

api_main = Blueprint('main-api', __name__, url_prefix='main-api')


class GamesAPI(MethodView):

    def __init__(self) -> None:
        self.GAMES_PER_PAGE = 8
        self.GAMES_PER_PAGE_MAX = 24
        self.SIZE = Game.query.count()
        print(self.SIZE)
        super().__init__()

    def get(self, id=None):
        for k,v in request.args.items():
            print(f"[{k}: {v}], ")
        page = request.args.get('page', 1, int)
        print(f"page = {page}")
        if id:
            game = Game.query.get_or_404(id)
            return jsonify(game=dataclasses.asdict(game)), 200
        else:
            from flask_sqlalchemy import Pagination
            games: Pagination = Game.query.paginate(page=page, per_page=self.GAMES_PER_PAGE, max_per_page=self.GAMES_PER_PAGE_MAX)
            paginated_games = games.items
            games_dict = dict()
            for i, game in enumerate(paginated_games):
                games_dict[i] = dataclasses.asdict(game)
        return jsonify(games=games_dict, total=len(games_dict), games_remaining=self.SIZE-len(games_dict)), 200

    def post(self, key=None):
        """
        `steam_web_api_key`: NEED TO GRAB IT FROM HEADER or QUERY;

        :param key: steam_web_api_key
        :returns: list[dict]
        """
        # @app.before_first_request
        def addSteamGames():
            import random, csv
            from markupsafe import Markup
            from steam import webapi
            from Backend.app import app
            from Backend.app import steam_web_api_key

            deleted_rows = Game.query.delete()
            logging.warning(f"{deleted_rows} ROWS WERE DELETED FROM `GAME`")
            games: List[Game] = []
            ids = []
            players_min_count = []
            with open(path.join(app.root_path, 'resources', 'games.csv'), 'r') as game_data:
                for row in csv.reader(game_data):
                    ids.append(int(row[0]))
                    players_min_count.append(int(row[1]))
            logging.info('GAME IDS TO BE ADDED: ' + ', '.join(map(str, ids)))
            logging.info('GAME PLAYERS_COUNT TO BE ADDED: ' + ', '.join(map(str, players_min_count)))
            for step, _id in enumerate(ids):
                url = f"https://store.steampowered.com/api/appdetails/?appids={_id}&key={key}&l=russian"
                response: dict = webapi.webapi_request(url)
                game_info = response[f'{_id}']['data']
                name: str = game_info['name']
                sd: str = Markup(game_info['short_description'])
                players_count: int = players_min_count[step]
                price: int = random.randint(0, 1)
                # rating = None
                preview_url: str = f"https://steamcdn-a.akamaihd.net/steam/apps/{_id}/header.jpg"
                game = Game(id=_id, name=name, short_description=sd, players_count=players_count, price=price,
                            preview_url=preview_url)
                games.append(game)
            try:
                db.session.add_all(games)
                db.session.commit()
            except Exception as e:
                logging.exception("AN ERROR OCCURRED WHILE ADDING GAME", exc_info=e)
            finally:
                uploaded_games = Game.query.all()
                games_db = dict()
                for i, game in enumerate(games_db):
                    games_db[i] = dataclasses.asdict(game)
                _json = jsonify(total=len(games), games=games_db)
                logging.info(_json)
                return _json, 200
        return addSteamGames()


catalog = GamesAPI.as_view("catalog")
api_main.add_url_rule("/catalog", endpoint="catalog", view_func=catalog, methods=["GET"])
api_main.add_url_rule("/catalog/upload", endpoint="catalog", view_func=catalog, methods=["POST"])
api_main.add_url_rule("/game/<int:id>", endpoint="game", view_func=catalog, methods=["GET"])


class HelperAPI(Resource):
    # @swag_from("swagger/helper/get.yaml", validation=True)
    def get(self):
        genres = request.args.getlist("genres")
        players_count = int(request.args.get("players_count"))
        min_price = int(request.args.get("min_price"))
        max_price = int(request.args.get("max_price"))

        args = dict()
        for arg in request.args:
            args[f"{arg}"] = request.args[arg]

        filtered_games: list = Game.query.filter_by(**args).order_by(Game.rating)

        # db.Query().join(Game)
        # data = db.session.query(Game)\
        #     .filter(
        #     Game.price.in_((min_price, max_price)),
        #     Game.players_count == players_count) \
        #     .all()
            # .filter(
            # Genre.name.in_(genres)
            # )\
            # .all()
        return jsonify(data=filtered_games), 200

    # @swag_from("./swagger/helper/post.yaml")
    def post(self):
        pass


helper = HelperAPI.as_view("helper")
api_main.add_url_rule("/helper", view_func=helper, methods=["GET"])


# @api.resource("/profile")
class ProfileAPI(Resource):
    def get(self, id=None):
        ids = request.args.get("ids", type=list)
        print(ids)
        users: tuple
        if id and "id" in request.path:
            user = User.query.get_or_404(id)
            return jsonify(user=user), 200
        elif ids:
            from sqlalchemy.orm import session
            users = User.query.filter(User.id.in_(ids))
        else:
            users = User.query.all()
        return jsonify(users=list(map(lambda user_: {f"user_{user_.id}": dataclasses.asdict(user_)}, users)))

    def post(self):
        pass


profile = ProfileAPI.as_view("profile")
api_main.add_url_rule("/profile/<int:id>", view_func=profile, methods=["GET"])
api_main.add_url_rule("/users", view_func=profile, methods=["GET", "POST"])


# @api.resource("/login")
class LoginAPI(Resource):
    def get(self):
        pass

    def post(self):
        from werkzeug.security import check_password_hash
        if request.method == "POST":
            email = request.form['login-mail']
            password = request.form['password']
            user = User.query.filter_by(login_mail=email).first()
            if not user or not check_password_hash(user.pass_hash, password):
                return jsonify(response="Bad password or email", code=400), 400
            else:
                return jsonify(user), 200


login = LoginAPI.as_view("login")
api_main.add_url_rule("/login", view_func=login, methods=["GET", "POST"])


# @api.resource("/registrate")
class RegistrateAPI(Resource):
    def get(self):
        pass

    def post(self):
        from werkzeug.security import generate_password_hash
        if request.method == "POST":
            if request.form['password'] == request.form['password2']:
                user = User(nickname=request.form['nickname'], login_mail=request.form['login-mail'],
                            pass_hash=generate_password_hash(request.form['password']))
                try:
                    db.session.add(user)
                    db.session.commit()
                except sqlite3.Error as e:
                    return e.__repr__(), 400
                return jsonify(user)
            else:
                return jsonify(reponse={"message": "User already exists"}), 400


registrate = RegistrateAPI.as_view("registrate")
api_main.add_url_rule("/registrate", view_func=registrate, methods=["GET", "POST"])


# @api.resource("/change-pass")
class ChangePassAPI(Resource):
    def __init__(self) -> None:
        self.req_parse = reqparse.RequestParser()
        self.req_parse.add_argument('new_password', type=str, required=True, location='form',
                                    help='New password can`t be empty!')
        self.req_parse.add_argument('new_password2', type=str, required=True, location='form',
                                    help='Please enter new password once again!')
        self.req_parse.add_argument('old_password', type=str, required=True, location='form',
                                    help='Old password can`t be empty!')
        super(ChangePassAPI, self).__init__()

    def get(self):
        pass

    def post(self):
        from flask_login import current_user
        from werkzeug.security import check_password_hash
        from werkzeug.security import generate_password_hash

        args = self.req_parse.parse_args()
        user = User.query.get(current_user.id)
        old_pass = args.get("old_password")
        new_pass = args.get("new_password")
        new_pass2 = args.get("new_password2")
        if check_password_hash(user.pass_hash, old_pass) and \
                new_pass == new_pass2:
            user.pass_hash = generate_password_hash(new_pass)
            db.session.commit()
        return jsonify(dataclasses.asdict(user))


change_pass = LoginAPI.as_view("change-pass")
api_main.add_url_rule("/change-pass", view_func=change_pass, methods=["GET", "POST"])
# from Backend.app import api
# api.add_resource(GamesAPI, "/catalog", "/game/<int:id>", endpoint="games")
# api.add_resource(HelperAPI, "/helper", endpoint="helper")
# api.add_resource(ProfileAPI, "/helper", endpoint="helper")
# api.add_resource(LoginAPI, "/helper", endpoint="helper")
# api.add_resource(RegistrateAPI, "/helper", endpoint="helper")
