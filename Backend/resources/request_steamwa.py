import json
import requests


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

