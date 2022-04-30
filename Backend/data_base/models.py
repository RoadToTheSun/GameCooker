from flask_security import UserMixin
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass

db = SQLAlchemy()

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )

user_games = db.Table('user_games',
                      db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                      db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                      db.Column('user_rating', db.Integer()),
                      db.Column('favourite', db.Boolean())
                      )



@dataclass
class Role(db.Model, UserMixin):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True)
    description: str = db.Column(db.String(100))


game_genres = db.Table('game_genres',
                       db.Column('game_id', db.Integer(), db.ForeignKey('game.id')),
                       db.Column('genre_id', db.Integer(), db.ForeignKey('genre.id'))
                       )


@dataclass
class Genre(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)


@dataclass
class Game(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    players_count: int = db.Column(db.Integer, nullable=False)
    price: int = db.Column(db.Integer, nullable=False)
    rating: int = db.Column(db.Integer, nullable=True)
    preview_url: str = db.Column(db.VARCHAR)
    genres: Genre = db.relationship('Genre', secondary=game_genres, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return self.name


@dataclass
class User(db.Model, UserMixin):
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nickname: str = db.Column(db.String(100))
    login_mail: str = db.Column(db.String(100), unique=True)
    pass_hash: str = db.Column(db.String(255), nullable=False)
    roles: Role = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    users_rating: Game = db.relationship('Game', secondary=user_games, backref=db.backref('users', lazy='dynamic'))

# db.create_all(app.app)
