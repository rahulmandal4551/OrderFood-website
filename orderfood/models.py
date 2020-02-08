from flask import redirect, url_for
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from orderfood import db, login_manager, app, admin
from flask_login import UserMixin, current_user
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key= True)
    username = db.Column(db.String(50), nullable= False)
    email = db.Column(db.String(100), unique= True, nullable= False)
    phone_no = db.Column(db.String(15), nullable=False) 
    administrator_access = db.Column(db.Boolean, nullable= False, default= False)
    image_file = db.Column(db.String(20), nullable= False, default='default_img.jpg')
    password = db.Column(db.String(60), nullable= False)
    address = db.Column(db.Text, nullable= False)
    order_json = db.Column(db.Text, default=None)
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    all_orders = db.relationship('Orders', backref='ordered_by', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id' : self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.phone_no}', '{self.address}')"

class Food_item(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(200), nullable= False)
    details = db.Column(db.Text, default=None)
    availability = db.Column(db.Integer, nullable= False, default= 0)
    price = db.Column(db.Float, nullable= False, default= 0.0)
    current_requirement = db.Column(db.Integer, nullable= False, default=0)

    def __repr__(self):
        return f"Food Item('{self.title}', '{self.price}', 'avail:{self.availability}', 'req:{self.current_requirements}')"

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable= False)
    order_json = db.Column(db.Text, nullable=False)
    order_details = db.Column(db.Text, default=None) # for complete overview of order like- name, address of user,
                                                    #  quantity and details of food items, total price, delivery info
    price = db.Column(db.Float, nullable= False, default= 0.0)
    # Payment Method options 0: Not Available, 1: Paytm Payment Gateway, 2: Direct Online(UPI), 3: COD
    payment_method = db.Column(db.Integer, nullable= False, default= 0)
    # Payment Status options 0: Payment Pending, 1: Payment Successful, 2: Payment Failed
    payment_status = db.Column(db.Integer, nullable= False, default= 0)
    payment_details = db.Column(db.Text, default=None)
    is_completed = db.Column(db.Boolean, nullable= False, default= False)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    remarks = db.Column(db.Text, default=None)

    def __repr__(self):
        return f"Order('{self.order_json}','{self.user_id}', '{self.price}','{self.date_ordered}', '{self.payment_method}', '{self.payment_status}', '{self.is_completed}')"

class Not_Verified_User(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    username = db.Column(db.String(50), nullable= False)
    email = db.Column(db.String(100), unique= True, nullable= False)
    phone_no = db.Column(db.String(15), nullable=False) 
    password = db.Column(db.String(60), nullable= False)
    address = db.Column(db.Text, nullable= False)
    last_verification_email_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def get_email_verify_token(self, expires_sec=86400):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'verify_user_id' : self.id}).decode('utf-8')

    @staticmethod
    def verify_email_verify_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['verify_user_id']
        except:
            return None
        return Not_Verified_User.query.get(user_id)

    def __repr__(self):
        return f"Not Verified User('{self.username}', '{self.email}', '{self.phone_no}','{self.last_verification_email_time}', '{self.address}')"

# Views for Flask-Admin Panel
class MyModelView(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))

class UserModelView(ModelView):
    column_searchable_list = ('username', 'email')
    column_display_pk = True

    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))

class Food_itemModelView(ModelView):
    column_searchable_list = ('title', 'details')
    column_display_pk = True

    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))

class OrderModelView(ModelView):
    column_display_pk = True
    column_searchable_list = ('user_id', 'date_ordered', 'order_details')
    form_choices = { 
                    'payment_method': [('0', 'Not Available'), ('1', 'Payment Gateway(Paytm)'), ('2', 'Direct Online(UPI)'), ('3', 'COD')],
                    'payment_status': [('0', 'Pending'), ('1', 'Successful'), ('2', 'Failed')],
                   }
    column_choices = {
                        'payment_method': [(0, 'Not Available'), (1, 'Payment Gateway(Paytm)'), (2, 'Direct Online(UPI)'), (3, 'COD')], 
                        'payment_status': [(0, 'Pending'), (1, 'Successful'), (2, 'Failed')]
                    }

    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))

class NotificationsView(BaseView):
    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))
            
    @expose('/')
    def index(self):
        return self.render('admin/notifs.html')

admin.add_view(UserModelView(User, db.session))
admin.add_view(Food_itemModelView(Food_item, db.session))
admin.add_view(UserModelView(Not_Verified_User, db.session))
admin.add_view(OrderModelView(Orders, db.session))
admin.add_view(NotificationsView(name='Notifications', endpoint='notifs'))