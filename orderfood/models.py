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
    image_file = db.Column(db.String(20), nullable= False, default='default_img.jpg')
    password = db.Column(db.String(60), nullable= False)
    address = db.Column(db.Text, nullable= False)
    order_json = db.Column(db.Text, default=None)
    administrator_access = db.Column(db.Boolean, nullable= False, default= False)
    past_orders = db.Column(db.Text, default=None)
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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
        return f"User('{self.username}', '{self.email}', '{self.phone_no}', '{self.image_file}', '{self.address}')"

class Food_item(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(200), nullable= False)
    details = db.Column(db.Text)
    availability = db.Column(db.Integer, nullable= False, default= 0)
    price = db.Column(db.Float, nullable= False, default= 0.0)

    def __repr__(self):
        return f"Food Item('{self.title}', '{self.price}', '{self.availability}')"

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
        return f"Not_Verified_User('{self.username}', '{self.email}', '{self.phone_no}','{self.last_verification_email_time}', '{self.address}')"

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
admin.add_view(NotificationsView(name='Notifications', endpoint='notifs'))