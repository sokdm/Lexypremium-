from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, PasswordField, BooleanField, SubmitField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from flask_wtf.file import FileAllowed, FileRequired

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    price = FloatField('Price (₦)', validators=[DataRequired(), NumberRange(min=0)])
    original_price = FloatField('Original Price (₦) [Optional]', validators=[Optional(), NumberRange(min=0)])
    length = StringField('Length (e.g., 20 inches)', validators=[Optional(), Length(max=20)])
    description = TextAreaField('Description', validators=[DataRequired()])
    short_description = TextAreaField('Short Description (Max 200 chars)', validators=[Optional(), Length(max=200)])
    stock = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)], default=10)
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    is_featured = BooleanField('Featured Product')
    is_active = BooleanField('Active', default=True)
    images = MultipleFileField('Product Images', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')])
    submit = SubmitField('Save Product')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class CheckoutForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Delivery Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired(), Length(max=50)])
    state = SelectField('State', choices=[
        ('Lagos', 'Lagos'),
        ('Abuja', 'Abuja FCT'),
        ('Rivers', 'Rivers'),
        ('Oyo', 'Oyo'),
        ('Kano', 'Kano'),
        ('Delta', 'Delta'),
        ('Ogun', 'Ogun'),
        ('Kaduna', 'Kaduna'),
        ('Edo', 'Edo'),
        ('Anambra', 'Anambra'),
        ('Other', 'Other State')
    ], validators=[DataRequired()])
    submit = SubmitField('Proceed to Payment')

class OrderStatusForm(FlaskForm):
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ])
    payment_status = SelectField('Payment Status', choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ])
    notes = TextAreaField('Admin Notes')
    submit = SubmitField('Update Order')

class SettingsForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired()])
    store_phone = StringField('Store Phone/WhatsApp', validators=[DataRequired()])
    store_email = StringField('Store Email', validators=[DataRequired(), Email()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    bank_account = StringField('Bank Account Number', validators=[DataRequired()])
    bank_account_name = StringField('Account Name', validators=[DataRequired()])
    submit = SubmitField('Save Settings')
