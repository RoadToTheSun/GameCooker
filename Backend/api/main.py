import dataclasses
import sqlite3

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
    # @swag_from("swagger/catalog/get.yaml", )
    # @swag_from("swagger/game/get.yaml", )
    # @api_main.get("catalog")
    # @api_main.get("game/<int:id>")
    def get(self, id=None):
        from flask_sqlalchemy import orm
        games = Game.query.all() \
            if id is None else Game.query.get_or_404(id)
        games_dict: dict = dict()
        for i, game in enumerate(games):
            games_dict[f"game_{i}"] = dataclasses.asdict(game)
        return jsonify(games=games_dict)

    # def post(self, id):
    #
    #     pass


catalog = GamesAPI.as_view("catalog")
api_main.add_url_rule("/catalog", endpoint="catalog", view_func=catalog, methods=["GET"])
api_main.add_url_rule("/game/<int:id>", endpoint="game", view_func=catalog, methods=["GET", "POST"])


class HelperAPI(Resource):
    # @swag_from("swagger/helper/get.yaml", validation=True)
    def get(self):
        genres = request.args.getlist("genres")
        players_count = int(request.args.get("players_count"))
        min_price = int(request.args.get("min_price"))
        max_price = int(request.args.get("max_price"))

        filtered_games: list = Game.query.all()
        if players_count or min_price or max_price:
            if players_count:
                filtered_games.filter(Game.players_count==players_count)
            if min_price:
                filtered_games.filter(Game.price>=min_price)
            if max_price:
                filtered_games.filter(Game.price<=max_price)
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
