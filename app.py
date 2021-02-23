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
secret_code = "admin1"

init_db()
login_manager.init_app(app)

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'login_id' in current_user.__dict__:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        special_code = request.form.get('administrator_code')
        confirm_password = request.form.get('confirm_password')
        if confirm_password != password:
            return redirect(url_for('register'))

        password = generate_password_hash(password)

        print(special_code)

        if special_code == secret_code:
            user = User(email=email, username=username, password=password, special_code=special_code)
        else:    
            user = User(email=email, username=username, password=password)
        
        db_session.add(user)
        db_session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_id' in current_user.__dict__:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if not user:
            flash("No such user!")
            return redirect(url_for('login'))

        if not check_password_hash(user.password, request.form.get('password')):
            flash("Wrong password!")
            return redirect(url_for('login'))

        if user and check_password_hash(user.password, request.form.get('password')):
            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)

        return redirect(url_for('home'))

    return render_template('login.html')
    
@app.route("/logout")
@login_required
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('home'))
    
    
    
    
    
    
    