from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, FloatField, SelectField, DateField, validators
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime, timedelta

class ListingForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=10, max=2000, message='Description must be between 10 and 2000 characters')
    ])
    
    price = FloatField('Price (₹)', validators=[
        DataRequired(message='Price is required'),
        NumberRange(min=1, max=100000, message='Price must be between ₹1 and ₹100,000')
    ])
    
    quality = SelectField('Quality', choices=[
        ('Like New', 'Like New'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor')
    ], validators=[DataRequired(message='Please select quality')])
    
    category = SelectField('Category', choices=[
        ('Books', 'Books'),
        ('Electronics', 'Electronics'),
        ('Furniture', 'Furniture'),
        ('Clothing', 'Clothing'),
        ('Sports', 'Sports & Fitness'),
        ('Kitchen', 'Kitchen & Dining'),
        ('Stationery', 'Stationery'),
        ('Decor', 'Home Decor'),
        ('Other', 'Other')
    ], validators=[DataRequired(message='Please select a category')])
    
    tags = StringField('Tags (comma-separated, max 5)', validators=[
        Optional(),
        Length(max=200, message='Tags must be less than 200 characters')
    ])
    
    images = MultipleFileField('Images (up to 3)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only JPG, JPEG, PNG, and GIF files are allowed'),
        Optional()
    ])
    
    expires_at = DateField('Listing Expires On', validators=[
        DataRequired(message='Please select an expiry date')
    ], default=lambda: (datetime.utcnow() + timedelta(days=30)).date())
    
    def validate_expires_at(self, field):
        if field.data:
            # Convert date to datetime for comparison
            expiry_datetime = datetime.combine(field.data, datetime.min.time())
            if expiry_datetime <= datetime.utcnow():
                raise ValidationError('Expiry date must be in the future')
            if expiry_datetime > datetime.utcnow() + timedelta(days=365):
                raise ValidationError('Expiry date cannot be more than 1 year from now')
    
    def validate_tags(self, field):
        if field.data:
            tags = [tag.strip() for tag in field.data.split(',') if tag.strip()]
            if len(tags) > 5:
                raise validators.ValidationError('Maximum 5 tags allowed')
    
    def validate_images(self, field):
        if field.data:
            images = [img for img in field.data if img.filename]
            if len(images) > 3:
                raise validators.ValidationError('Maximum 3 images allowed')

class ProfileForm(FlaskForm):
    username = StringField('Display Name', validators=[
        DataRequired(message='Display name is required'),
        Length(min=2, max=64, message='Display name must be between 2 and 64 characters')
    ])
    
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500, message='Bio must be less than 500 characters')
    ])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(min=10, max=20, message='Phone number must be between 10 and 20 characters')
    ])
