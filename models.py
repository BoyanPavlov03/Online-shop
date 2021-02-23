from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from sqlalchemy import Column, Integer, String
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
        if special_code:
            return True

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
