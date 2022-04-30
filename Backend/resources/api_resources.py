import logging
import traceback

from flask_restful import Resource, Api, reqparse
from flask import current_app, jsonify
from sqlalchemy.exc import NoResultFound

from Backend.app import steam_api

api = Api(current_app)

@api.handle_error(Exception(NoResultFound))
def db_not_found(e):
    logging.warning(traceback.format_exc())
    return {'message' : 'DB result was not found'}, 404

@api.resource('/apilist')
class SupportedAPIList(Resource):

    def get(self):
        """get interfaces with their methods
        Allows to get all steam_api available interfaces with their methods
        :returns: json
        """
        # parser = reqparse.RequestParser()
        # parser.add_argument()
        response = steam_api.call('ISteamWebAPIUtil.GetSupportedAPIList')

        interfaces: list = steam_api.interfaces
        logging.info(', '.join([str(i.doc()) for i in interfaces]))
        return jsonify(response)
