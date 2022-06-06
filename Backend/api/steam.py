from flask import Flask, Blueprint
from flask_restful import Resource, Api, reqparse
from flask import jsonify

# import flask_marshmallow
import logging

from flasgger import swag_from
from steam import webapi

api_steam = Blueprint('steam-api', __name__)


# @swag_from("swagger/apilist/get.yaml", "yaml", endpoint="apilist", methods=["GET"])
@api_steam.route("/apilist", methods=["GET"])
def get_supported_steam_api_list():
    from Backend.app import steam_api
    response = steam_api.call('ISteamWebAPIUtil.GetSupportedAPIList')
    interfaces: list = steam_api.interfaces
    # logging.info(', '.join([str(i.doc()) for i in interfaces]))
    return jsonify(response)


# @swag_from("swagger/apps/get.yaml")
@api_steam.route("/apps", methods=["GET"])
def get_apps_from_store_service():
    from Backend.app import steam_api
    response = steam_api.call('IStoreService.GetAppList')
    # logging.info(response)
    return jsonify(response)


# @swag_from("swagger/apps/get.yaml")
@api_steam.route("/apps/<int:app_id>", methods=["GET"])
def get_app_info(app_id, key=None, l="russian"):
    # from Backend.app import steam_api, steam_web_api_key
    url = f"https://store.steampowered.com/api/appdetails/?appids={app_id}&key={key}&l={l}"
    response: dict = webapi.webapi_request(url)
    game_info = response[f'{app_id}']['data']
    return jsonify(game_info)
