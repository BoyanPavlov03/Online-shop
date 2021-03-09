from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, current_user, logout_user
import uuid

from models import User, Product, Address, Category, Cart, Wish, Rating
from login import login_manager
from database import db
from flask_msearch import Search

app = Flask (__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WHOOSH_BASE"]='whoosh'
app.secret_key = "safdgsrtbywrtybytjnbhw5yh5646454"
secret_code = "admin1"

db.init_app(app)
search = Search()
search.init_app(app)
with app.app_context():
    db.create_all()

login_manager.init_app(app)

@app.route('/')
def index():
    return redirect(url_for('home'))
    
@app.route('/home')
def home():
    return render_template("index.html",categories = Category.query.all(),products = Product.query.all())
        
@app.route('/search', methods=['GET','POST'])
def search():  
    keyword = request.form.get('q')
    
    result = Product.query.msearch(keyword,fields=['name'])
    
    return render_template("index.html",products=result,categories = Category.query.all())
    
@app.route('/addrating/<int:product_id>', methods=['GET','POST'])
@login_required
def addrating(product_id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        rating = float(rating)
        if rating > 5 or rating < 0:
            return redirect(url_for('product',product_id=product_id))
        
        checker = Rating.query.filter_by(user_id=current_user.id).filter_by(product_id=product_id).first()
        if checker:
            return redirect(url_for('product',product_id=product_id))
        
        r = Rating(user_id=current_user.id,product_id=product_id,rating=rating)
        product = Product.query.filter_by(id=product_id).first()
        product.rating_count += 1
        
        db.session.add(r)
        db.session.commit()
        
    return redirect(url_for('product',product_id=product_id))
    

@app.route('/addcart/<int:product_id>', methods=['GET','POST'])
@login_required
def addcart(product_id):
    cart = Cart(user_id=current_user.id,product_id=product_id)
    db.session.add(cart)
    db.session.commit()
    
    return redirect(url_for('home'))
    
@app.route('/addcartfromwish/<int:product_id>', methods=['GET','POST'])
@login_required
def addcartfromwish(product_id):
    cart = Cart(user_id=current_user.id,product_id=product_id)
    db.session.add(cart)
    db.session.commit()
    
    return redirect(url_for('wishlist',user_id=current_user.id))
    
@app.route('/addcartfromproduct/<int:product_id>', methods=['GET','POST'])
@login_required
def addcartfromproduct(product_id):
    cart = Cart(user_id=current_user.id,product_id=product_id)
    db.session.add(cart)
    db.session.commit()
    
    return redirect(url_for('product',product_id=product_id))
    
@app.route('/addwishfromproduct/<int:product_id>', methods=['GET','POST'])
@login_required
def addwishfromproduct(product_id):
    wish = Wish(user_id=current_user.id,product_id=product_id)
    db.session.add(wish)
    db.session.commit()
    
    return redirect(url_for('product',product_id=product_id))
    
@app.route("/removecart/<int:product_id>", methods=['GET', 'POST'])
@login_required
def removecart(product_id):
    cart = Cart.query.filter_by(product_id=product_id).first()
    db.session.delete(cart)
    db.session.commit()

    return redirect(url_for('cart',user_id=current_user.id))
    
@app.route('/addwish/<int:product_id>', methods=['GET','POST'])
@login_required
def addwish(product_id):
    wish = Wish(user_id=current_user.id,product_id=product_id)
    db.session.add(wish)
    db.session.commit()
    
    return redirect(url_for('home'))
    
@app.route("/removewish/<int:product_id>", methods=['GET', 'POST'])
@login_required
def removewish(product_id):
    wish = Wish.query.filter_by(product_id=product_id).first()
    db.session.delete(wish)
    db.session.commit()

    return redirect(url_for('wishlist',user_id=current_user.id))
    
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

        category = Category(name=name)
        
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
        short_description = request.form.get('short_description')
        description = request.form.get('description')
        price = request.form.get('price')
        category = request.form.get('category')
        
        product_check = Product.query.filter_by(name=name).first()
        if product_check:
            flash("This product exists!","danger")
            return redirect(url_for('newproduct'))
            
        product = Product(name=name,short_description=short_description,description=description,price=price,rating=0,category_id=category)
    
        db.session.add(product)
        db.session.commit()
        
        return redirect(url_for('home'))
        
    return render_template('newproduct.html',categories = Category.query.all())

@app.route('/product/<int:product_id>')
def product(product_id):
    ratings=Rating.query.filter_by(product_id=product_id).all()
    product=Product.query.filter_by(id=product_id).first()
    category=Category.query.filter_by(id=product.category_id).first()
    
    total = 0
    for r in ratings:
        total += r.rating
    
    if product.rating_count != 0:
        product.rating = total / product.rating_count
    
    return render_template("product_details.html",product=product,category=category)

@app.route('/cart/<int:user_id>')
@login_required
def cart(user_id):
    if user_id != current_user.id:
        return redirect(url_for('home'))
        
    result=db.session.query(Product,Cart).filter(Cart.user_id == current_user.id).outerjoin(Product, Product.id == Cart.product_id).all()
    total = 0
    for r in result:
        total += r[0].price
    
    return render_template("cart.html",products=result,total=total)
    
@app.route('/wishlist/<int:user_id>')
@login_required
def wishlist(user_id):
    if user_id != current_user.id:
        return redirect(url_for('home'))
        
    result=db.session.query(Product,Wish).filter(Wish.user_id == current_user.id).outerjoin(Product, Product.id == Wish.product_id).all()
    
    return render_template("wishlist.html",products=result)
    
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
    
@app.route('/myaddress/<int:user_id>', methods=['GET', 'POST'])
@login_required
def myaddress(user_id):
    address_check = Address.query.filter_by(user_id=current_user.id).first()
    if request.method == "POST":
        town = request.form.get('town')
        street = request.form.get('street')
        delivery = request.form.get('delivery')
        postal_code = request.form.get('postal_code')
        
        if not address_check:
            address = Address(town=town,street=street,delivery=delivery,postal_code=postal_code,user_id=user_id)
            db.session.add(address)
        else:
            address_check.town = town
            address_check.street = street
            address_check.delivery = delivery
            address_check.postal_code = postal_code
                
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("address.html",address=Address.query.filter_by(user_id=current_user.id).first())
    
@app.route("/logout")
@login_required
def logout():
    current_user.login_id = None
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))