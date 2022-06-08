#
#
# def addSteamGames():
#     import random, itertools, csv
#     # def uniqueid():
#     #     seed = random.getrandbits(18)
#     #     while True:
#     #         yield seed
#     #         seed += 1
#     #
#     # unique_sequence = uniqueid()
#     # ids = list(itertools.islice(unique_sequence, 10))
#     # db.delete(Game)
#     ids = []
#     with open(path.join(parent_dir, path.join('resources', 'games.csv')), 'r') as games:
#         for _id in csv.reader(games):
#             ids.append(_id[0])
#     logging.info(', '.join(ids))
#     for _id in ids:
#         url = f"https://store.steampowered.com/api/appdetails/?appids={_id}&key={steam_web_api_key}&l=russian"
#         response: dict = webapi.webapi_request(url)
#         game = response[f'{_id}']['data']
#         name: str = game['name']
#         players_count: int = random.randint(1, 10)
#         price: int = random.randint(0, 1)
#         # rating = None
#         preview_url: str = f"https://steamcdn-a.akamaihd.net/steam/apps/{_id}/header.jpg"
#         db.session.add(Game(id=_id, name=name, players_count=players_count, price=price, preview_url=preview_url))
#     try:
#         db.session.commit()
#     except Exception as e:
#         logging.exception("AN ERROR OCCURRED WHILE ADDING GAME", exc_info=e)