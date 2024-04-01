from datetime import datetime
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
from sqlalchemy import UniqueConstraint
import jwt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    categories = db.relationship('Category', backref='user', lazy='dynamic')
    recipes = db.relationship('Recipe', backref='user', lazy='dynamic')
    shop_lists = db.relationship('Shoplist', backref='user', lazy='dynamic')
    list_items = db.relationship('Listitem', backref='user', lazy='dynamic')
    planned_meals = db.relationship('MealRecipe', backref='user', lazy='dynamic')
    pref_size = db.Column(db.Integer)
    pref_sort = db.Column(db.Integer)
    pref_picture = db.Column(db.Integer)
    pref_color = db.Column(db.Integer)
    pref_theme = db.Column(db.Integer)
    reg_time = db.Column(db.DateTime)
    last_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hex_id = db.Column(db.String(8), nullable=False, unique=True)
    title = db.Column(db.String(80), nullable=False, index=True)
    category = db.Column(db.Integer, db.ForeignKey('category.id'))
    photo = db.Column(db.String(100))
    description = db.Column(db.String(500))
    url = db.Column(db.String(200))
    servings = db.Column(db.Integer)
    prep_time = db.Column(db.Integer)
    cook_time = db.Column(db.Integer)
    total_time = db.Column(db.Integer)
    ingredients = db.Column(db.String(2200))
    instructions = db.Column(db.String(6600))
    time_created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    favorite = db.Column(db.Integer)
    public = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class NutritionalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    calories = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    protein = db.Column(db.Integer)
    fat = db.Column(db.Integer)
    sugar = db.Column(db.Integer)
    cholesterol = db.Column(db.Integer)
    sodium = db.Column(db.Integer)
    fiber = db.Column(db.Integer)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hex_id = db.Column(db.String(8), nullable=False)
    label = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    __table_args__ = (db.UniqueConstraint('hex_id', name='cat_hexid_unique'), )

    def __repr__(self):
        return '<Category {}>'.format(self.label)

class Shoplist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hex_id = db.Column(db.String(8), nullable=False, unique=True)
    label = db.Column(db.String(20), nullable=False)
    list_items = db.relationship('Listitem', backref='shoplist', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Shoplist {}>'.format(self.label)

class Listitem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hex_id = db.Column(db.String(10), nullable=False, unique=True)
    item = db.Column(db.String(100), nullable=False)
    rec_title = db.Column(db.String(80))
    complete = db.Column(db.Integer)
    list_id = db.Column(db.Integer, db.ForeignKey('shoplist.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class MealRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hex_id = db.Column(db.String(10), nullable=False, unique=True)
    date = db.Column(db.String(10), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
