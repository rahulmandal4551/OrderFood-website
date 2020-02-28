import secrets
import os
import json
import requests
from datetime import datetime, time
from pytz import timezone
from PIL import Image
from flask import render_template, jsonify, url_for, flash, redirect, request, abort
from orderfood import app, db, bcrypt, mail
from orderfood.models import User, Food_item, Not_Verified_User, Orders
from orderfood.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestPasswordResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from orderfood.config import Config
from flask_mail import Message
from orderfood import CheckSum

India_TimeZone = timezone('Asia/Kolkata')

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
        if datetime.now(India_TimeZone).time() < time(19,30,0) and datetime.now(India_TimeZone).time() > time(15,0,0):
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
        else:
            flash("Order can only placed between 3 PM to 7:30 PM", 'info')
            return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html', title= 'About')

delivery_charges = 10.0

def calcPriceJSON(ordered_item_dict):
    price = None
    if ordered_item_dict:
        price = 0.0
        for key, val in ordered_item_dict.items():
            price += Food_item.query.get(int(key)).price * val
        price += delivery_charges
    return price

def calcPriceDetailsJSON(ordered_item_dict):
    total_price = 0.0
    order_details = ""
    for key, val in ordered_item_dict.items():
        total_price += Food_item.query.get(int(key)).price * val
        order_details += f'{Food_item.query.get(int(key)).title} : {val} ; '

    total_price += delivery_charges
    order_details += f'Delivery Charges : ₹{delivery_charges} \n'
    return total_price, order_details

def send_verification_email(user):
    token = user.get_email_verify_token()
    msg = Message('OrderFood Account Email Verification', 
                    sender=('OrderFood', Config.MAIL_USERNAME), 
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
        price = None
        order_details = None
        try:
            ordered_item_dict = json.loads(current_user.order_json)
            price, order_details = calcPriceDetailsJSON(ordered_item_dict)
            order_details = order_details.split(';')
        except:
            pass

    image_file = url_for('static', filename= f"profile_pics/{current_user.image_file}")
    return render_template('account.html', title='Account', image_file=image_file, form=form, price=price, order_details=order_details , all_orders=current_user.all_orders)

def send_reset_password_email(user):
    token = user.get_reset_token()
    msg = Message('OrderFood Password Reset Request', 
                    sender=('OrderFood',Config.MAIL_USERNAME), 
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

@app.route('/payment_options')
@login_required
def payment_options():
    if datetime.now(India_TimeZone).time() < time(19,30,0) and datetime.now(India_TimeZone).time() > time(15,0,0):
        ordered_item_dict = None
        price = None
        order_details = None
        try:
            ordered_item_dict = json.loads(current_user.order_json)
            price, order_details = calcPriceDetailsJSON(ordered_item_dict)
            order_details = order_details.split(';')
        except:
            pass

        if ordered_item_dict:
            return render_template('payment_options.html', title='Payment Options', order_details=order_details, price= price)
        else:
            return redirect(url_for('home')) 
    else:
            flash("Order can only placed between 3 PM to 7:30 PM", 'info')
            return redirect(url_for('home'))

@app.route('/paytm_payment_gateway')
@login_required
def payment_ptm():
    ordered_item_dict = None
    try:
        ordered_item_dict = json.loads(current_user.order_json)
    except:
        return redirect(url_for('home')) 

    total_price = None
    if ordered_item_dict:
        total_price, order_details = calcPriceDetailsJSON(ordered_item_dict)

        new_order = Orders(user_id=current_user.id, order_json= current_user.order_json, order_details=order_details, price=total_price, payment_method=1, payment_status=0, date_ordered= datetime.now(India_TimeZone))
        db.session.add(new_order)
        current_user.order_json = None
        db.session.commit()

    # initialize dictionary with request parameters
    paytmParams = {
        # Find your MID in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
        "MID" : Config.PAYTM_TEST_MERCHANT_ID,
        # Find your WEBSITE in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
        "WEBSITE" : "WEBSTAGING",
        # Find your INDUSTRY_TYPE_ID in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
        "INDUSTRY_TYPE_ID" : "Retail",
        # WEB for website and WAP for Mobile-websites or App
        "CHANNEL_ID" : "WEB",
        # Enter your unique order id
        "ORDER_ID" : str(new_order.id),
        # unique id that belongs to your customer
        "CUST_ID" : str(current_user.id),
        # customer's mobile number
        "MOBILE_NO" : current_user.phone_no,
        # customer's email
        "EMAIL" : current_user.email,
        # Amount in INR that is payble by customer
        # this should be numeric with optionally having two decimal points
        "TXN_AMOUNT" : str(new_order.price),
        # on completion of transaction, we will send you the response on this URL
        "CALLBACK_URL" : url_for("ptmcallback", _external=True),
    }
    print('paytmParams', paytmParams)
    # Generate checksum for parameters we have
    # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
    checksum = CheckSum.generate_checksum(paytmParams, Config.PAYTM_TEST_SECRET_KEY)

    # for Staging
    url = "https://securegw-stage.paytm.in/order/process"

    # for Production
    # url = "https://securegw.paytm.in/order/process"
    return render_template('paytm_payment_gateway.html',url=url, paytmParams=paytmParams, checksum=checksum)

@app.route('/ptmcallback', methods=['GET', 'POST'])
@login_required
def ptmcallback():
    if request.method == 'POST':
        received_data = request.form.to_dict()
        paytmChecksum = ""
        # Create a Dictionary from the parameters received in POST
        # received_data should contains all data received in POST
        paytmParams = {}
        for key, value in received_data.items(): 
            if key == 'CHECKSUMHASH':
                paytmChecksum = value
            else:
                paytmParams[key] = value
        print("received_data", received_data)
        # Verify checksum
        # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys 
        isValidChecksum = CheckSum.verify_checksum(paytmParams, Config.PAYTM_TEST_SECRET_KEY, paytmChecksum)
        new_order_id = paytmParams['ORDERID']
        if isValidChecksum:
            print("Checksum Matched")
            if received_data['STATUS'] == 'TXN_FAILURE':
                new_order = Orders.query.get(new_order_id)
                new_order.payment_status = 2
                new_order.payment_details = json.dumps(received_data)
                db.session.commit()
                print(str(received_data))
                return redirect(url_for("order_details", order_id = new_order_id))
            else:    
                paytmParams = dict()
                # Find your MID in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
                paytmParams["MID"] = Config.PAYTM_TEST_MERCHANT_ID
                # Enter your order id which needs to be check status for
                paytmParams["ORDERID"] = new_order_id
                # Generate checksum by parameters we have
                # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys 
                checksum = CheckSum.generate_checksum(paytmParams, Config.PAYTM_TEST_SECRET_KEY)
                # put generated checksum value here
                paytmParams["CHECKSUMHASH"] = checksum
                # prepare JSON string for request
                post_data = json.dumps(paytmParams)

                # for Staging
                url = "https://securegw-stage.paytm.in/order/status"

                # for Production
                # url = "https://securegw.paytm.in/order/status"

                response = requests.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()            
                print("response", response)
                new_order = Orders.query.get(new_order_id)
                if response['STATUS'] == 'TXN_SUCCESS':
                    new_order.payment_status = 1
                    new_order.payment_details = json.dumps(response)
                    db.session.commit()
                    print(str(received_data) + "\n*******************************\n" + str(response))
                    return redirect(url_for("order_details", order_id = new_order_id))
                elif response['STATUS'] == 'TXN_FAILURE':
                    new_order.payment_status = 2
                    new_order.payment_details = json.dumps(response)
                    db.session.commit()
                    print(str(received_data) + "\n*******************************\n" + str(response))
                    return redirect(url_for("order_details", order_id = new_order_id))
        else:
            print("Checksum Mismatched")
            return redirect(url_for("order_details", order_id = new_order_id))

    elif request.method == 'GET':
        return redirect(url_for('home'))

# @app.route('/payment_direct')
# @login_required
# def payment_direct():
#     ordered_item_dict = None
#     try:
#         ordered_item_dict = json.loads(current_user.order_json)
#     except:
#         return redirect(url_for('home')) 

#     total_price = None
#     if ordered_item_dict:
#         total_price, order_details = calcPriceDetailsJSON(ordered_item_dict)
#         # print(order_details)
#         new_order = Orders(user_id=current_user.id, order_json= current_user.order_json, order_details=order_details, price=total_price, payment_method=2, payment_status=0, date_ordered= datetime.now(India_TimeZone))
#         db.session.add(new_order)
#         current_user.order_json = None
#         db.session.commit()
#     return render_template('payment_direct.html', title='Payment Direct', order_id = new_order.id)

@app.route("/order_details/<order_id>" , methods=['GET', 'POST'])
@login_required
def order_details(order_id):
        order = Orders.query.get_or_404(order_id)
        if (order.user_id != current_user.id) and (not current_user.administrator_access):
            abort(403)

        # if payment method is Paytm Payment Gateway is used and payment staus is still pending, check again using Transaction API
        if order.payment_method == 1 and order.payment_status == 0:
            paytmParams = dict()
            # Find your MID in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
            paytmParams["MID"] = Config.PAYTM_TEST_MERCHANT_ID
            # Enter your order id which needs to be check status for
            paytmParams["ORDERID"] = order_id
            # Generate checksum by parameters we have
            # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys 
            checksum = CheckSum.generate_checksum(paytmParams, Config.PAYTM_TEST_SECRET_KEY)
            # put generated checksum value here
            paytmParams["CHECKSUMHASH"] = checksum
            # prepare JSON string for request
            post_data = json.dumps(paytmParams)

            # for Staging
            url = "https://securegw-stage.paytm.in/order/status"

            # for Production
            # url = "https://securegw.paytm.in/order/status"

            response = requests.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()            
            print("response", response)
            new_order = Orders.query.get(order_id)
            if response['STATUS'] == 'TXN_SUCCESS':
                new_order.payment_status = 1
                new_order.payment_details = json.dumps(response)
                db.session.commit()
            elif response['STATUS'] == 'TXN_FAILURE':
                new_order.payment_status = 2
                new_order.payment_details = json.dumps(response)
                db.session.commit()
        
        return render_template('order_details.html', title='Order Details', order=order)

@app.route('/payment_cod')
@login_required
def payment_cod():
    ordered_item_dict = None
    try:
        ordered_item_dict = json.loads(current_user.order_json)
    except:
        pass
    total_price = None
    if ordered_item_dict:
        total_price, order_details = calcPriceDetailsJSON(ordered_item_dict)

        new_order = Orders(user_id=current_user.id, order_json= current_user.order_json, order_details=order_details, price=total_price, payment_method=3, payment_status=0, date_ordered= datetime.now(India_TimeZone))
        db.session.add(new_order)
        current_user.order_json = None
        db.session.commit()
        return render_template('payment_cod.html', title='Payment COD', price=total_price, order_id = new_order.id)
    else:
        return redirect(url_for('home'))    
