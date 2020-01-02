from orderfood import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key= True)
    username = db.Column(db.String(50), nullable= False)
    email = db.Column(db.String(100), unique= True, nullable= False)
    image_file = db.Column(db.String(20), nullable= False, default='default_img.jpg')
    password = db.Column(db.String(60), nullable= False)
    address = db.Column(db.Text, nullable= False)
    order_json = db.Column(db.Text, default=None)
    # past_orders = db.Column(db.Text, default=None)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.address}')"

class Food_item(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(200), nullable= False)
    details = db.Column(db.Text)
    availability = db.Column(db.Integer, nullable= False, default= 0)
    price = db.Column(db.Float, nullable= False, default= 0.0)

    def __repr__(self):
        return f"Food Item('{self.title}', '{self.price}', '{self.availability}')"
