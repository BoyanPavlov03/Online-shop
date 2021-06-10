from flask import Flask,request,session,url_for,redirect,render_template,make_response,flash,json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, current_user, logout_user
import uuid
import os
from sqlalchemy import text
from threading import Thread


from models import User, Product, Address, Category, Cart, Wish, Rating, PromoCode
from login import login_manager
from database import db
from flask_msearch import Search
from recommendations import sim_pearson,topMatches,transformPrefs
from decorator import check_confirmed
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

uploads = os.path.join('static','img')

app = Flask (__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "safdgsrtbywrtybytjnbhw5yh5646454"
app.config['UPLOAD_FOLDER'] = uploads

sender_mail = 'tues.komisarite@abv.bg'
sender_pass = 'komisarite123'

mail_settings = {
    "MAIL_SERVER": 'smtp.abv.bg',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": sender_mail,
    "MAIL_PASSWORD": sender_pass
}

app.config.update(mail_settings)

db.init_app(app)
search = Search()
search.init_app(app)

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

with app.app_context():
    db.create_all()
    admin = User(email="admin@gmail.com",username="admin",password=generate_password_hash("1234"),is_admin=1,confirmed=True,admin_activation=True)
    admin_check = User.query.filter_by(email=admin.email).first()
    if not admin_check:
        db.session.add(admin)
        db.session.commit()

app.add_url_rule('/uploads/<filename>', 'uploaded_file', build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads':  app.config['UPLOAD_FOLDER']
})

login_manager.init_app(app)

def get_total_price():
    result = db.session.query(Product,Cart).filter(Cart.user_id == current_user.id).outerjoin(Product, Product.id == Cart.product_id).all()
    quantity = Cart.query.filter_by(user_id=current_user.id).all()

    total = 0
    i = 0
    for r in result:
        total += r[0].price * quantity[i].quantity
        i += 1

    return total

def validate_file_type(filename, allowed_types):
    return filename.split(".")[-1] in allowed_types

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(email):
    token = serializer.dumps(email, salt='email-confirm')
    msg = Message('Confirm Email', sender=sender_mail, recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = f'Click here to confirm email {link}'
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()

def newsletter(product, email):
    msg = Message('A new product has been added', sender=sender_mail, recipients=[email])
    link = url_for('product', product_id=str(product.id), _external=True)
    msg.body = f'Here is a link to the new product {link}'
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()

@app.route('/deactivate/<int:user_id>')
def deactivate(user_id):
    if current_user.id == user_id:
        user = User.query.filter_by(id=user_id).first()
        user.received = False

        db.session.commit()

    return redirect(url_for('home'))

@app.route('/activate/<int:user_id>')
def activate(user_id):
    if current_user.id == user_id:
        user = User.query.filter_by(id=user_id).first()
        user.received = True

        db.session.commit()

    return redirect(url_for('home'))

@app.route('/resend/<int:user_id>')
def resend(user_id):
    user = User.query.filter_by(id=user_id).first()
    send_email(user.email)

    return redirect(url_for('unconfirmed'))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    return render_template("unconfirmed.html")

@app.route('/confirm_email/<token>', methods=['GET','POST'])
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('The link for the confirmation is expired! Please register again!', 'danger')
        return '<h1>The link has expired! Sorry :(</h1>'

    user = User.query.filter_by(email=email).first()
    if not user.confirmed:
        user.confirmed = True
        db.session.commit()
    return redirect(url_for('logout'))

@app.route('/admin_register', methods=['GET','POST'])
def admin_register():
    if current_user.id != 1:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        user_check = User.query.filter_by(email=email).first()
        if user_check:
            flash("Email already exists! Sign in!","danger")
            return redirect(url_for('admin_register'))

        user_check = User.query.filter_by(username=username).first()
        if user_check:
            flash("Username already exists! Sign in!","danger")
            return redirect(url_for('admin_register'))

        if confirm_password != password:
            flash("Passwords doesn't match","danger")
            return redirect(url_for('admin_register'))

        password = generate_password_hash(password)

        user = User(email=email,username=username,password=password,is_admin=1)

        db.session.add(user)
        db.session.commit()

        send_email(email)

        return redirect(url_for('home'))

    return render_template("admin_register.html")

@app.route('/admin_list', methods=['GET', 'POST'])
def admin_list():
    if not current_user.is_main_admin:
        return redirect(url_for('home'))

    users = User.query.filter_by(is_admin=1, confirmed=1).all()

    return render_template("list_admins.html",users=users)

@app.route('/activation/<int:user_id>/<int:purpose>')
def activation(user_id, purpose):
    if not current_user.is_main_admin:
        return redirect(url_for('home'))

    user = User.query.filter_by(id=user_id).first()

    print(purpose)

    if purpose:
        user.admin_activation = True
    else:
        user.admin_activation = False

    db.session.commit()

    return redirect(url_for('admin_list'))

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template("index.html",categories = Category.query.all(),products = Product.query.all())

@app.route('/checkout/<int:user_id>', methods=['GET','POST'])
def checkout(user_id):
    if user_id != current_user.id:
        return redirect(url_for('home'))

    address = Address.query.filter_by(user_id=user_id).first()
    test = 0
    if address:
        if address.town and address.street and address.postal_code and address.delivery:
            test = 1

    if request.method == 'POST':
        db.session.execute("delete from cart where user_id = "+ str(user_id) + ";")
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("checkout.html", address=address, test=test)

@app.route('/search', methods=['GET','POST'])
def search():
    keyword = request.form.get('q')

    result = Product.query.msearch(keyword,fields=['name'])

    return render_template("index.html",products=result,categories = Category.query.all(),q=keyword)

@app.route('/addrating/<int:product_id>', methods=['GET','POST'])
@login_required
@check_confirmed
def addrating(product_id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        rating = float(rating)
        if rating > 5 or rating < 0:
            return redirect(url_for('product',product_id=product_id))

        checker = Rating.query.filter_by(user_id=current_user.id).filter_by(product_id=product_id).first()
        if checker:
            return redirect(url_for('product',product_id=product_id))

        r = Rating(user_id=current_user.id,product_id=product_id,rating=rating,comment=comment)
        product = Product.query.filter_by(id=product_id).first()
        product.rating_count += 1

        db.session.add(r)
        db.session.commit()

    return redirect(url_for('product',product_id=product_id))

@app.route('/applypromocode', methods=['GET','POST'])
def applypromocode():
    data = request.form
    name = data['name']
    code = PromoCode.query.filter_by(name=name).first()
    total = get_total_price()

    if not code:
        return json.dumps(total)

    if total > 15:
        if code.type == "percentage":
            total = total - (total*code.value/100)
        else:
            total -= code.value

    total = round(total, 2)

    return json.dumps(total)

@app.route('/addcart', methods=['GET','POST'])
@login_required
@check_confirmed
def addcart():
    data = request.form
    product = Product.query.filter_by(id=int(data['product_id'])).first()
    product_price = int(data['quantity'])*product.price
    cart = Cart(user_id=current_user.id,product_id=int(data['product_id']),quantity=int(data['quantity']),price=product_price)
    if cart.quantity < 0:
        return {}

    product = Cart.query.filter_by(product_id=cart.product_id, user_id=current_user.id).first()
    if product:
        product.quantity += cart.quantity
        product.price += product_price

        db.session.commit()
        return {}

    if cart.quantity != 0:
        db.session.add(cart)
        db.session.commit()

    return {}

@app.route("/removecart", methods=['GET', 'POST'])
@login_required
@check_confirmed
def removecart():
    data = request.form
    cart = Cart.query.filter_by(product_id=int(data['product_id']),user_id=current_user.id).first()
    db.session.delete(cart)
    db.session.commit()

    total = get_total_price()

    checker = 1

    cart = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart:
        checker = 0

    return {"index":int(data['product_id']),"checker":checker,"total":total}

@app.route('/addwish', methods=['GET','POST'])
@login_required
@check_confirmed
def addwish():
    data = request.form
    wish = Wish(user_id=current_user.id,product_id=int(data['product_id']))
    product = Wish.query.filter_by(product_id=wish.product_id, user_id = current_user.id).first()

    if not product:
        db.session.add(wish)
        db.session.commit()

    return {}

@app.route("/removewish", methods=['GET', 'POST'])
@login_required
@check_confirmed
def removewish():
    data = request.form
    wish = Wish.query.filter_by(product_id=int(data['product_id']),user_id=current_user.id).first()
    db.session.delete(wish)
    db.session.commit()

    checker = 1

    cart = Wish.query.filter_by(user_id=current_user.id).all()
    if not cart:
        checker = 0

    return {"index":int(data['product_id']),"checker":checker}

@app.route('/promocode', methods=['GET', 'POST'])
@login_required
@check_confirmed
def promocode():
    if current_user.is_activated == False:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        type = request.form.get('type')
        amount = request.form.get('amount')
        code_check = PromoCode.query.filter_by(name=name).first()
        if code_check:
            flash("This code exists!","danger")
            return redirect(url_for('promocode'))

        promocode = PromoCode(name=name,type=type,value=amount)
        db.session.add(promocode)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('promocode.html')

@app.route('/newcategory', methods=['GET', 'POST'])
@login_required
@check_confirmed
def newcategory():
    if current_user.is_activated == False:
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
@check_confirmed
def newproduct():
    if current_user.is_activated == False:
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

        image = "static\img\p1.jpg"
        if 'image' in request.files and request.files['image']:
            upload = request.files['image']
            filename = secure_filename(upload.filename)
            if validate_file_type(filename, ["jpeg", "jpg", "png"]):
                upload.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = f"{app.config['UPLOAD_FOLDER']}\{filename}"

        product = Product(name=name,short_description=short_description,description=description,price=price,rating=0,category_id=category,img=image)
        db.session.add(product)
        db.session.commit()

        users = User.query.filter_by(received=True).all()
        product = Product.query.filter_by(name=name).first()

        for user in users:
            newsletter(product, user.email, user.id)

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

    product.rating = round(product.rating, 2)

    total = 0

    users = []
    comments = []
    rating = []

    ratings = db.engine.execute(text("select User.username, Rating.rating, Rating.comment from Rating left join User on Rating.user_id = User.id where Rating.product_id = " + str(product_id)))
    for r in ratings:
        rating.append(r[1])
        users.append(r[0])
        comments.append(r[2])
        total += 1

    ratings = Rating.query.all()
    recommended_products = {}

    for i in range(len(ratings)):
        user = User.query.filter_by(id=ratings[i].user_id).first()
        product_check = Product.query.filter_by(id=ratings[i].product_id).first()

        if user.username not in recommended_products.keys():
            recommended_products[user.username] = {}

        if product_check.name not in recommended_products[user.username].keys():
            recommended_products[user.username][product_check.name] = ratings[i].rating

    recommended_products = transformPrefs(recommended_products)
    if product.name not in recommended_products:
        product_list = []
    else:
        recommended_products = topMatches(recommended_products,product.name,4)
        product_list = [Product.query.filter_by(name=product[1]).first() for product in recommended_products]

    return render_template("product_details.html",recommended_products=product_list,product=product,category=category,ratings=rating,users=users,comments=comments,total=total)

@app.route('/cart/<int:user_id>')
@login_required
@check_confirmed
def cart(user_id):
    if user_id != current_user.id:
        return redirect(url_for('home'))

    result = db.session.query(Product,Cart).filter(Cart.user_id == current_user.id).outerjoin(Product, Product.id == Cart.product_id).all()
    quantity = Cart.query.filter_by(user_id=current_user.id).all()

    total = 0
    i = 0
    for r in result:
        total += r[0].price * quantity[i].quantity
        i += 1

    return render_template("cart.html",products=result,total=total,quantity=quantity)

@app.route('/wishlist/<int:user_id>')
@login_required
@check_confirmed
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

        user = User(email=email,username=username,password=password)

        db.session.add(user)
        db.session.commit()

        send_email(email)

        return redirect(url_for('home'))

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
@check_confirmed
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
