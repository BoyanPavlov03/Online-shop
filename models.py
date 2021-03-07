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
    special_code = db.Column(db.String(6), nullable=True)

    @property
    def is_administrator(self):
        if self.special_code:
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

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), unique=True, nullable=False)
    count = db.Column(Integer, unique=False, nullable=True, default=0)

class Product(db.Model):
    __searchable__ = ['name']
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(800), unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    rating =  db.Column(db.String(80), unique=False, nullable=False)
    category_id = db.Column(db.Integer, ForeignKey("category.id"))
    carts = db.relationship('Cart', backref='product')
    
class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    product_id = db.Column(db.Integer, ForeignKey('product.id'))
    
class Wish(db.Model):
    __tablename__ = 'wish'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    product_id = db.Column(db.Integer, ForeignKey('product.id'))
    
class Address(db.Model):
    __tablename__ = 'address'
    id = db.Column(db.Integer, primary_key=True)
    postal_code = db.Column(db.String(10), unique=True, nullable=False)
    town = db.Column(db.String(80), unique=True, nullable=False)
    street = db.Column(db.String(150), unique=True, nullable=False)
    delivery = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))