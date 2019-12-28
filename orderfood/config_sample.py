# Please edit this file and save it with your own config details
# After editing you must rename this to "config.py" to start the Flask app Server 
import os

class Config:
    SECRET_KEY = 'secret' # Edit and Provide your own secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///demo.db' # Edit and Provide your own database path
