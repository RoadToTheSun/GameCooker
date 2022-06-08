from typing import List

from flask_security import UserMixin
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeMeta
import json


class OutputMixin(object):
    RELATIONSHIPS_TO_DICT = False

    def __iter__(self):
        return self.to_dict().items()

    def to_dict(self, rel=None, backref=None):
        if rel is None:
            rel = self.RELATIONSHIPS_TO_DICT
        res = {column.key: getattr(self, attr)
               for attr, column in self.__mapper__.c.items()}
        if rel:
            for attr, relation in self.__mapper__.relationships.items():
                # Avoid recursive loop between to tables.
                if backref == relation.table:
                    continue
                value = getattr(self, attr)
                if value is None:
                    res[relation.key] = None
                elif isinstance(value.__class__, DeclarativeMeta):
                    res[relation.key] = value.to_dict(backref=self.__table__)
                else:
                    res[relation.key] = [i.to_dict(backref=self.__table__)
                                         for i in value]
        return res

    def to_json(self, rel=None):
        def extended_encoder(attr_type):
            from datetime import datetime
            from uuid import UUID
            if isinstance(attr_type, datetime):
                return attr_type.isoformat()
            if isinstance(attr_type, UUID):
                return str(attr_type)

        if rel is None:
            rel = self.RELATIONSHIPS_TO_DICT
        return json.dumps(self.to_dict(rel), default=extended_encoder)


db = SQLAlchemy()

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )

user_games = db.Table('user_games',
                      db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                      db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                      db.Column('user_rating', db.Integer()),
                      db.Column('favourite', db.Boolean()),
                      PrimaryKeyConstraint('user_id', 'game_id', name='user_games_pk')
                      )


@dataclass
class Role(db.Model, UserMixin):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True)
    description: str = db.Column(db.String(100))


game_genres = db.Table('game_genres',
                       db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                       db.Column('genre_id', db.Integer(), db.ForeignKey('genre.id')),
                       PrimaryKeyConstraint('game_id', 'genre_id', name='game_genres_pk')
                       )


@dataclass
class Genre(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)

    # games = db.relationship('Game', secondary=game_genres, backref=db.backref('g_genres', lazy='dynamic'),
    #                         primaryjoin=id == game_genres.c.genre_id
    #                         # secondaryjoin=id == game_genres.c.genre_id
    #                         )

    def __hash__(self):
        return self.id

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name


@dataclass
class Game(db.Model):
    RELATIONSHIPS_TO_DICT = True

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    short_description: str = db.Column(db.VARCHAR, nullable=True)
    players_count: int = db.Column(db.Integer, nullable=False)
    price: int = db.Column(db.Integer, nullable=False)
    rating: int = db.Column(db.Integer, nullable=True)
    preview_url: str = db.Column(db.VARCHAR)
    genres = db.relationship('Genre', secondary=game_genres, backref=db.backref('games', lazy='dynamic'),
                             # primaryjoin=id == game_genres.c.game_id
                             # secondaryjoin=id == game_genres.c.genre_id
                             )

    def __str__(self):
        return f"{self.id}, {self.name}, {self.rating}"

    def __repr__(self):
        return self.name


@dataclass
class User(db.Model, UserMixin):
    RELATIONSHIPS_TO_DICT = True

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nickname: str = db.Column(db.String(100), unique=True)
    login_mail: str = db.Column(db.String(100), unique=True)
    pass_hash: str = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    users_rating = db.relationship('Game', secondary=user_games,
                                   backref=db.backref('users', lazy='dynamic'))
    active: bool = db.Column(db.Boolean)

    # def has_role(self, role):
    #     return self.role in roles_users

    def get_id(self):
        return self.id

    def hash_password(self):
        from werkzeug.security import generate_password_hash
        self.pass_hash = generate_password_hash(self.password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

    def from_dict(self, data, new_user=False):
        for field in ['nickname', 'login_mail', 'pass_hash']:
            if field in data:
                setattr(self, field, data[field])
# db.create_all(app.app)
