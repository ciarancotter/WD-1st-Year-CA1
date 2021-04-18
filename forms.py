from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, DecimalField, IntegerField, SelectField
from wtforms.validators import InputRequired, EqualTo

choices = ['Shaggy', 'Wombat', 'Popcat', 'Fat Monke', 'Water Monke', 'Dance Monke', 'Oogway', 'The Shining', 'Homer', 'Squidward']

class RegistrationForm(FlaskForm):
    user_id = StringField("User ID:",validators=[InputRequired()])
    password = PasswordField("Password:",validators=[InputRequired()])
    password2 = PasswordField("Confirm Password:",validators=[InputRequired(), EqualTo("password")])
    bio = StringField("Profile Bio:",validators=[InputRequired()])
    pfp = SelectField("Profile Picture:", choices=choices, validators=[InputRequired()])
    submit = SubmitField("Submit")

class EmployeeRegistrationForm(FlaskForm):
    employee_id = StringField("Employee ID:",validators=[InputRequired()])
    password = PasswordField("Password:",validators=[InputRequired()])
    secret = PasswordField("Secret Pass:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    user_id = StringField("User ID:",validators=[InputRequired()])
    password = PasswordField("Password:",validators=[InputRequired()])
    submit = SubmitField("Submit")


class EmployeeForm(FlaskForm):
    employee_id = StringField("Employee ID:",validators=[InputRequired()])
    password = PasswordField("Password:",validators=[InputRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    currentPass = PasswordField("Current Password:", validators=[InputRequired()])
    newPass = PasswordField("New Password:", validators=[InputRequired()])
    newPassAgain = PasswordField("New Password Again:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class BookingForm(FlaskForm):
    row = IntegerField("Row:", validators=[InputRequired()])
    column = IntegerField("Column:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class TransferForm(FlaskForm):
    recipient = StringField("Recipient:", validators=[InputRequired()])
    amount = DecimalField("Amount:", validators=[InputRequired()])
    submit = SubmitField("Send")

class FriendForm(FlaskForm):
    friend = StringField("Add friend:", validators=[InputRequired()])
    submit = SubmitField("Send")

class LoanForm(FlaskForm):
    amount = IntegerField("Loan amount:",validators=[InputRequired()])
    submit = SubmitField("Request")

class EditProfilePage(FlaskForm):
    bio = StringField("Enter your bio:", validators=[InputRequired()])
    pfp = SelectField("Profile Picture:", choices=choices, validators=[InputRequired()])
    submit = SubmitField("Submit")