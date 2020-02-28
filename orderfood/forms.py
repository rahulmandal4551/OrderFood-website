from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from orderfood.models import User, Not_Verified_User

class RegistrationForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(), Length(min= 3, max= 50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_no = StringField('Phone No: (+91)', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min= 4, max= 15)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min= 4, max= 15), EqualTo('password')])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That Email is already taken. Please choose a different one.')
        NVuser = Not_Verified_User.query.filter_by(email=email.data).first()
        if NVuser:
            raise ValidationError('That Email is already taken. Please choose a different one.')
    
    def validate_phone_no(self, phone_no):
        p = phone_no.data
        if len(p)==10:
            for i in p:
                if not(ord(i)>=ord('0') and ord(i)<=ord('9')):
                    raise ValidationError('Please Enter a Valid Phone Number')
            if p[0] not in ['6', '7', '8', '9']:
                raise ValidationError('Please Enter a Valid Phone Number')
        elif len(p)==11:
            for i in p:
                if not(ord(i)>=ord('0') and ord(i)<=ord('9')):
                    raise ValidationError('Please Enter a Valid Phone Number')
            if p[0] != '0' or p[1] not in ['6', '7', '8', '9']:
                raise ValidationError('Please Enter a Valid Phone Number')
        else:
            raise ValidationError('Please Enter a Valid Phone Number')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min= 4, max= 15)])
    remember = BooleanField('Remember Me', default="checked")
    submit = SubmitField('Log In')

class UpdateAccountForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(), Length(min= 3, max= 50)])
    address = TextAreaField('Address', validators=[DataRequired()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must Register first.')
        NVuser = Not_Verified_User.query.filter_by(email=email.data).first()
        if NVuser:
            raise ValidationError('Your Email is not verified. Check your email to activate your Account.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min= 4, max= 15)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min= 4, max= 15), EqualTo('password')])
    submit = SubmitField('Reset Password')