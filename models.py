from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from database import db
from sqlalchemy import Column, Integer, String, ForeignKey, Float

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)
    login_id = db.Column(db.String(36), nullable=True)
    is_admin = db.Column(db.Integer, default=0, unique=False)

    @property
    def is_administrator(self):
        if self.is_admin:
            return True
        return False

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.login_id

    def __repr__(self):
        return '<User %r>' % self.username    
        
class PromoCode(db.Model):
    __tablename__ = 'promocode'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(50), unique=False, nullable=False)
    value = db.Column(db.Integer, unique=False, nullable=False)
    
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Product(db.Model):
    __tablename__ = 'product'
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    short_description = db.Column(db.String(80), unique=False, nullable=False)
    description = db.Column(db.String(800), unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    img = db.Column(db.String(50), unique=False, nullable=False)
    rating =  db.Column(db.Float, unique=False, nullable=False)
    rating_count = db.Column(Integer, unique=False, nullable=True, default=0)
    category_id = db.Column(db.Integer, ForeignKey("category.id"))

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, unique=False, default=1)
    price = db.Column(db.Float, unique=False, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    product_id = db.Column(db.Integer, ForeignKey('product.id'))
    
class Wish(db.Model):
    __tablename__ = 'wish'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    product_id = db.Column(db.Integer, ForeignKey('product.id'))
    
class Rating(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    product_id = db.Column(db.Integer, ForeignKey('product.id'))
    comment = db.Column(db.String(300), unique=False, nullable=False)
    rating =  db.Column(db.Integer, unique=False, nullable=False)
    
class Address(db.Model):
    __tablename__ = 'address'
    id = db.Column(db.Integer, primary_key=True)
    postal_code = db.Column(db.String(10), unique=False, nullable=False)
    town = db.Column(db.String(80), unique=False, nullable=False)
    street = db.Column(db.String(150), unique=False, nullable=False)
    delivery = db.Column(db.String(80), unique=False, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))