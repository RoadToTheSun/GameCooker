import json
import requests


def request_steam_web_api(interface, method, base_url="api.steampowered.com", version="v001",
                          http_method="GET", parameters: dict = None) -> dict:
    """How to Make a Steam Web API Request:

    Request URL format:

    ``https://{base_url}/{interface}/{method}/{version}?{parameters}``

    :param base_url: Usually ``https://api.steampowered.com``
    :param interface: Indicates which method group (interface) you want to use
    :param method: Indicates which method within the interface you want to use
    :param version: Indicates which version of the method you want to use
    :param http_method: GET / POST
    :param parameters: :optional: Parameters are delimited by the & character
    :return: Python dictionary object of response
    """

    # Already available from webapi module
    # from steam import webapi
    # response = webapi.webapi_request(f"https://{base_url}/{interface}/{method}/{version}", 'GET', params=parameters)
    response: requests.Response = requests.Response()
    if not parameters:
        parameters = {'format': 'json'}
    if http_method == "GET":
        response = requests.get(f"https://{base_url}/{interface}/{method}/{version}", parameters)
    elif http_method == "POST":
        response = requests.post(f"https://{base_url}/{interface}/{method}/{version}", parameters)
    response_dict = json.loads(response.text)
    return response_dict

