import secrets
import os
import json
from datetime import datetime
from PIL import Image
from flask import render_template, jsonify, url_for, flash, redirect, request
from orderfood import app, db, bcrypt, mail
from orderfood.models import User, Food_item, Not_Verified_User
from orderfood.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestPasswordResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        ordered_item_dict = None
        if current_user.is_authenticated:
            ordered_item_dict = json.loads(current_user.order_json) if current_user.order_json else None
        # print("ordered_item_dict", ordered_item_dict)
        return render_template('home.html', food_items=Food_item.query.all(), ordered_item_dict = ordered_item_dict )

    elif request.method == 'POST':
        orderDict = request.form.to_dict()
        if not current_user.is_authenticated:
            flash("Please log in to submit your Order", 'info')
            return redirect(url_for('login'))
        # print(f"Incoming JSON data converted to Dict {orderDict}")
        finalDict = {}
        for i in orderDict.keys():
            quantity = 0
            try:
                quantity = int(orderDict[i])
            except:
                quantity = int(float(orderDict[i]))
            if quantity > 0:
                finalDict[i.strip('qntid')] = quantity
        # print(finalDict)
        finalOrderJSON = json.dumps(finalDict)
        # print(finalOrderJSON, type(finalOrderJSON))
        current_user.order_json = finalOrderJSON if bool(finalDict) else None
        db.session.commit()
        flash("Your order has been updated!", 'success')
        return redirect(url_for('account'))

@app.route('/about')
def about():
    return render_template('about.html', title= 'About')

def send_verification_email(user):
    token = user.get_email_verify_token()
    msg = Message('OrderFood Account Email Verification', 
                    sender='noreply@demo.com', 
                    recipients=[user.email])

    msg.body = f'''To activate your OrderFood account, please visit the following Link:
{url_for('verify_email', token=token, _external=True)}

This Activation Link will be expired within 24 hours. So please be quick to activate your account. If this link is expired, then try to Log in({url_for('login',_external=True)}) and you'll receive new Activation Link.

If yot did not made this request then simply ignore this email.
'''
    mail.send(msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, address=form.address.data, phone_no=form.phone_no.data, date_registered=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        flash("Account created for {} ! You are now able to Log in".format(form.username.data), 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form= form, title= 'Register')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         NVuser = Not_Verified_User(username=form.username.data, email=form.email.data, password=hashed_password, address=form.address.data, phone_no=form.phone_no.data, last_verification_email_time=datetime.utcnow())       
#         db.session.add(NVuser)
#         db.session.commit()
#         send_verification_email(NVuser)
#         flash("An email has been sent with instructions to activate your Account.", 'info') 
#         return redirect(url_for('login'))
#     return render_template('register.html', form= form, title= 'Register')

@app.route("/verify_email/<token>")
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    NVuser = Not_Verified_User.verify_email_verify_token(token)
    if NVuser is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('register'))
    else:
        user = User(username=NVuser.username, email=NVuser.email, password=NVuser.password, address=NVuser.address, phone_no=NVuser.phone_no, date_registered=datetime.utcnow())       
        db.session.add(user)
        db.session.delete(NVuser)
        db.session.commit()
        flash("Account created for {} ! You are now able to Log in".format(user.username), 'success')
        return redirect(url_for('login'))

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
            NVuser = Not_Verified_User.query.filter_by(email=form.email.data).first()
            if NVuser:
                NVuser.last_verification_email_time = datetime.utcnow()
                db.session.commit()
                send_verification_email(NVuser)
                flash("Your Email is not verified. An email has been sent with instructions to activate your Account.", 'info') 
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
        current_user.address = form.address.data
        db.session.commit()
        flash("Your account has been updated!", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.address.data = current_user.address
        
        ordered_item_dict = None
        try:
            ordered_item_dict = json.loads(current_user.order_json)
        except:
            pass
    image_file = url_for('static', filename= f"profile_pics/{current_user.image_file}")
    return render_template('account.html', title='Account', image_file=image_file, form=form, ordered_item_dict=ordered_item_dict, food_items=Food_item.query.all())

def send_reset_password_email(user):
    token = user.get_reset_token()
    msg = Message('OrderFood Password Reset Request', 
                    sender='noreply@demo.com', 
                    recipients=[user.email])

    msg.body = f'''To Reset your password of your OrderFood account, please visit the following Link:
{url_for('reset_password', token=token, _external=True)}

This Reset Link will be expired within 30 minutes. So please be quick to reset the password.

If yot did not made this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/request_password_reset", methods=['GET', 'POST'])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_password_email(user)
        flash("An email has been sent with instructions to reset your password.", 'info')
        return redirect(url_for('login'))
    return render_template('request_password_reset.html', title="Request Password Reset", form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('request_password_reset'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated! You are now able to Log in", 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title="Reset Password", form=form)
