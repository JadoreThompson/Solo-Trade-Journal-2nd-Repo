from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import  InputRequired

class SignUpForm (FlaskForm):
    name = StringField('Name:', validators=[InputRequired()])
    email = EmailField('Email:', validators=[InputRequired()])
    password = PasswordField('Password:', validators=[InputRequired()])
    submit = SubmitField('Submit', validators=[InputRequired()])

class LoginForm (FlaskForm):
    email = EmailField('Email:', validators=[InputRequired()])
    password = PasswordField('Password:', validators=[InputRequired()])
    submit = SubmitField('Submit', validators=[InputRequired()])

