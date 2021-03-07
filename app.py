from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, current_user, logout_user
import uuid

from models import User, Product, Address, Category, Cart, Wish
from login import login_manager
from database import db

app = Flask (__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WHOOSH_BASE"]='whoosh'
app.secret_key = "safdgsrtbywrtybytjnbhw5yh5646454"
secret_code = "admin1"

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager.init_app(app)

@app.route('/')
def index():
    return redirect(url_for('home'))
    
@app.route('/home')
def home():
    return render_template("index.html" ,categories = Category.query.all(),products = Product.query.all())

@app.route('/addcart/<int:product_id>', methods=['GET','POST'])
@login_required
def addcart(product_id):
    cart = Cart(user_id=current_user.id,product_id=product_id)
    db.session.add(cart)
    db.session.commit()
    
    return redirect(url_for('home'))
    
@app.route('/addwish/<int:product_id>', methods=['GET','POST'])
@login_required
def addwish(product_id):
    wish = Wish(user_id=current_user.id,product_id=product_id)
    db.session.add(wish)
    db.session.commit()
    
    return redirect(url_for('home'))
    
@app.route('/newcategory', methods=['GET', 'POST'])
@login_required
def newcategory():
    if current_user.is_administrator == False:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('category')
        
        category_check = Category.query.filter_by(name=name).first()
        if category_check:
            flash("This category exists!","danger")
            return redirect(url_for('newcategory'))
            
        special_code = request.form.get('administrator_code')
        if special_code == secret_code:
            category = Category(name=name)
        else:
            return redirect(url_for('home'))
        
        db.session.add(category)
        db.session.commit()
        
        return redirect(url_for('home'))
        
    return render_template('newcategory.html')

@app.route('/newproduct', methods=['GET', 'POST'])
@login_required
def newproduct():
    if current_user.is_administrator == False:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('product')
        description = request.form.get('description')
        price = request.form.get('price')
        category = request.form.get('category')
        special_code = request.form.get('administrator_code')
        
        product_check = Product.query.filter_by(name=name).first()
        if product_check:
            flash("This product exists!","danger")
            return redirect(url_for('newproduct'))
        
        if special_code == secret_code:
            product = Product(name=name,description=description,price=price,rating=5,category_id=category)
        else:
            return redirect(url_for('home'))
        
        category = Category.query.filter_by(id=category).first()
        category.count += 1
    
        db.session.add(product)
        db.session.commit()
        
        return redirect(url_for('home'))
        
    return render_template('newproduct.html',categories = Category.query.all())

@app.route('/productdetails')
def productdetails():
    return render_template("product_details.html")

@app.route('/cart')
def cart():
    result=db.session.query(Product,Cart).outerjoin(Product, Product.id == Cart.product_id).all()
    total = 0
    for r in result:
        total += r[0].price
    
    return render_template("cart.html",products=result,total=total)
    
@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    products = Product.query.filter_by(category_id=category_id).all()
    categories = Category.query.all()
    return render_template("category.html",category=category,products=products,categories=categories)

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
        
        user_check = User.query.filter_by(email=email).first()
        if user_check:
            flash("Email already exists! Sign in!","danger")
            return redirect(url_for('register'))
        
        user_check = User.query.filter_by(username=username).first()
        if user_check:
            flash("Username already exists! Sign in!","danger")
            return redirect(url_for('register'))
            
        if confirm_password != password:
            flash("Passwords doesn't match","danger")
            return redirect(url_for('register'))

        password = generate_password_hash(password)

        if special_code == secret_code:
            user = User(email=email, username=username, password=password, special_code=special_code)
        else:    
            user = User(email=email, username=username, password=password)
        
        db.session.add(user)
        db.session.commit()

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
            db.session.commit()
            login_user(user)

        return redirect(url_for('home'))

    return render_template('login.html')
    
@app.route("/logout")
@login_required
def logout():
    current_user.login_id = None
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))