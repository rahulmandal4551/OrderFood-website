# Please edit this file and save it with your own config details
# After editing you must rename this to "config.py" to start the Flask app Server 
import os

class Config:
    SECRET_KEY = 'secret' # Edit and Provide your own secret key
    # Edit and Provide your own database path
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///sample.db' # For SQLite Database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://<USERNAME>:<PASSWORD>@localhost/<DATABASENAME>' # For MySQL database
    # For Installation of MySQL in Ubuntu: https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-18-04
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Following are the values for sending emails using a Gmail account.
    # If you use other email providers, you need to change these values
    
    # While sending Email using Gmail, you may get a Error (Google blocks less secure app that are trying to access Gmail)
    # In that case Turn On 'Less secure app access' from the link: https://myaccount.google.com/lesssecureapps

    MAIL_SERVER = 'smtp.gmail.com' # Enter the SMTP server address of your Email provider
    MAIL_PORT = 587 # Enter the SMTP port of your Email provider
    MAIL_USE_TLS = True # Use TLS security in your Email 

    MAIL_USERNAME = 'example@gmail.com' # Enter the Username of your Email account
    MAIL_PASSWORD = 'your password here' # Enter the Password of your Email account

    # In this website, we have used Paytm Payment Gateway( https://developer.paytm.com/docs/v1/payment-gateway/ ). 
    # To get the following values you should have Paytm Buisness Account. 
    # Find your MID in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
    PAYTM_TEST_MERCHANT_ID = 'sample_MID'
    # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
    PAYTM_TEST_SECRET_KEY = 'sample_secret_key'