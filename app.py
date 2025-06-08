import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///tiet_thrift.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google_auth.login'
login_manager.login_message = 'Please log in with your Thapar email to access this page.'

# Add custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML br tags"""
    if text is None:
        return ''
    return text.replace('\n', '<br>\n')

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import models and create tables
with app.app_context():
    import models
    db.create_all()

# Import and register blueprints
from google_auth import google_auth
app.register_blueprint(google_auth)

# Import utility functions
from utils import cleanup_expired_listings
from forms import ListingForm, ProfileForm

# Set up scheduler for automatic listing cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_expired_listings, trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    from models import Listing
    # Get recent listings for homepage
    recent_listings = Listing.query.filter(
        Listing.expires_at > datetime.utcnow()
    ).order_by(Listing.created_at.desc()).limit(6).all()
    
    return render_template('index.html', recent_listings=recent_listings)

@app.route('/listings')
def listings():
    from models import Listing
    
    # Get filter parameters
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search', '')
    quality = request.args.get('quality', '')
    
    # Base query for active listings
    query = Listing.query.filter(Listing.expires_at > datetime.utcnow())
    
    # Apply filters
    if category:
        query = query.filter(Listing.category == category)
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if search:
        query = query.filter(
            db.or_(
                Listing.title.contains(search),
                Listing.description.contains(search),
                Listing.tags.contains(search)
            )
        )
    if quality:
        query = query.filter(Listing.quality == quality)
    
    listings = query.order_by(Listing.created_at.desc()).all()
    
    # Get available categories and qualities for filters
    categories_from_db = db.session.query(Listing.category).filter(
        Listing.expires_at > datetime.utcnow()
    ).distinct().all()
    categories_from_db = [cat[0] for cat in categories_from_db if cat[0]]
    
    # Default categories from forms.py to ensure dropdown always has options
    default_categories = ['Books', 'Electronics', 'Furniture', 'Clothing', 'Sports', 'Kitchen', 'Stationery', 'Decor', 'Other']
    
    # Combine and deduplicate categories
    all_categories = list(set(categories_from_db + default_categories))
    all_categories.sort()
    
    qualities = ['Like New', 'Good', 'Fair', 'Poor']
    
    return render_template('listings.html', 
                         listings=listings, 
                         categories=all_categories,
                         qualities=qualities,
                         current_category=category,
                         current_quality=quality,
                         current_search=search,
                         current_min_price=min_price,
                         current_max_price=max_price)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    from models import Listing
    listing = Listing.query.get_or_404(listing_id)
    
    # Check if listing is still active
    if listing.expires_at <= datetime.utcnow():
        flash('This listing has expired.', 'warning')
        return redirect(url_for('listings'))
    
    # Get other listings from the same seller
    other_listings = Listing.query.filter(
        Listing.user_id == listing.user_id,
        Listing.id != listing.id,
        Listing.expires_at > datetime.utcnow()
    ).limit(4).all()
    
    return render_template('listing_detail.html', 
                         listing=listing, 
                         other_listings=other_listings)

@app.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = ListingForm()
    
    if form.validate_on_submit():
        from models import Listing
        from utils import save_images
        
        # Check if user email is verified Thapar domain
        if not current_user.email.endswith('@thapar.edu'):
            flash('Only verified Thapar University students can create listings.', 'error')
            return redirect(url_for('index'))
        
        # Save uploaded images
        image_urls = save_images(form.images.data)
        
        # Create new listing
        listing = Listing()
        listing.title = form.title.data
        listing.description = form.description.data
        listing.price = form.price.data
        listing.quality = form.quality.data
        listing.category = form.category.data
        listing.tags = form.tags.data
        listing.image_urls = ','.join(image_urls) if image_urls else ''
        listing.user_id = current_user.id
        listing.created_at = datetime.utcnow()
        listing.expires_at = datetime.utcnow() + timedelta(days=30)
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Your listing has been created successfully!', 'success')
        return redirect(url_for('listing_detail', listing_id=listing.id))
    
    return render_template('create_listing.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    from models import Listing
    
    # Get user's active listings
    active_listings = Listing.query.filter(
        Listing.user_id == current_user.id,
        Listing.expires_at > datetime.utcnow()
    ).order_by(Listing.created_at.desc()).all()
    
    # Get user's expired listings
    expired_listings = Listing.query.filter(
        Listing.user_id == current_user.id,
        Listing.expires_at <= datetime.utcnow()
    ).order_by(Listing.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         active_listings=active_listings,
                         expired_listings=expired_listings)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.phone = form.phone.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)

@app.route('/seller/<int:user_id>')
def seller_profile(user_id):
    from models import User, Listing
    
    seller = User.query.get_or_404(user_id)
    
    # Get seller's active listings
    listings = Listing.query.filter(
        Listing.user_id == user_id,
        Listing.expires_at > datetime.utcnow()
    ).order_by(Listing.created_at.desc()).all()
    
    return render_template('seller_profile.html', seller=seller, listings=listings)

@app.route('/delete_listing/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    from models import Listing
    
    listing = Listing.query.get_or_404(listing_id)
    
    # Check if current user owns this listing
    if listing.user_id != current_user.id:
        flash('You can only delete your own listings.', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted successfully.', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    from models import Listing
    from utils import save_images
    
    listing = Listing.query.get_or_404(listing_id)
    
    # Check if current user owns this listing
    if listing.user_id != current_user.id:
        flash('You can only edit your own listings.', 'error')
        return redirect(url_for('dashboard'))
    
    form = ListingForm(obj=listing)
    
    if form.validate_on_submit():
        listing.title = form.title.data
        listing.description = form.description.data
        listing.price = form.price.data
        listing.quality = form.quality.data
        listing.category = form.category.data
        listing.tags = form.tags.data
        
        # Handle new images if uploaded
        if form.images.data and any(img.filename for img in form.images.data):
            new_image_urls = save_images(form.images.data)
            if new_image_urls:
                listing.image_urls = ','.join(new_image_urls)
        
        db.session.commit()
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('listing_detail', listing_id=listing.id))
    
    return render_template('create_listing.html', form=form, listing=listing, edit_mode=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
