from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from sqlalchemy import Column, Integer, String, ForeignKey
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(80), unique=True, nullable=False)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(120), unique=True, nullable=False)
    login_id = Column(String(36), nullable=True)
    special_code = Column(String(6), nullable=True)

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

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(800), unique=False, nullable=False)
    price = Column(String(80), unique=False, nullable=False)
    rating =  Column(String(80), unique=False, nullable=False)
    shopping_id = Column(Integer, ForeignKey("user.id"))
    wish_id = Column(Integer, ForeignKey("user.id"))
    category_id = Column(Integer, ForeignKey("category.id"))
    
class Address(Base):
    __tablename__ = 'address'
    id = Column(Integer, primary_key=True)
    postal_code = Column(String(10), unique=True, nullable=False)
    town = Column(String(80), unique=True, nullable=False)
    street = Column(String(150), unique=True, nullable=False)
    delivery = Column(String(80), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))