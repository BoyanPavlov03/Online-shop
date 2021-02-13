from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, current_user, logout_user
import uuid
from sqlalchemy import asc
from datetime import datetime

from models import User
from login import login_manager
from database import db_session, init_db

app = Flask (__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "safdgsrtbywrtybytjnbhw5yh5646454"

init_db()
login_manager.init_app(app)