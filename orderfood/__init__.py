from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from orderfood.config import Config
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return (current_user.is_authenticated and current_user.administrator_access)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))

admin = Admin(app, 'OrderFood Admin', index_view=MyAdminIndexView())

from orderfood import routes