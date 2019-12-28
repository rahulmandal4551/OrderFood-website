import secrets
import os
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from orderfood import app, db, bcrypt
from orderfood.models import User, Food_item
from orderfood.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required

food_items = [
    {
        'Title' : 'Chicken Biriyani',
        'Details' : 'Chicken Biriyani(Leg Piece with Egg) from your favourite Resturant',
        'Price' : '₹ 100.00',
        'isAvailable' : 'Available'
    },
    {
        'Title' : 'Sattu Paratha',
        'Details' : 'Paratha stuffed with sattu from your favourite Resturant',
        'Price' : '₹ 10.00',
        'isAvailable' : 'Available'
    },
    {
        'Title' : 'Chilli Chicken',
        'Details' : 'Chilli Chicken (8 pieces) from your favourite Resturant',
        'Price' : '₹ 120.00',
        'isAvailable' : 'Not Available'
    }
]


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', food_items=Food_item.query.all())

@app.route('/about')
def about():
    return render_template('about.html', title= 'About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, address=form.address.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created for {} ! You are now able to Log in".format(form.username.data), 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form= form, title= 'Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash("Welcome {} ! Successfully Logged In.".format(user.username), 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login Failed. Please check your Email and Password", 'danger')
    return render_template('login.html', form= form, title= 'Login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex +  f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    # form_picture.save(picture_path)
    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.address = form.address.data
        db.session.commit()
        flash("Your account has been updated!", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
    image_file = url_for('static', filename= f"profile_pics/{current_user.image_file}")
    return render_template('account.html', title='Account', image_file=image_file, form=form)