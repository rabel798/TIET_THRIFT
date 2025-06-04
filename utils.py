import os
import uuid
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
from app import db

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (800, 800)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_images(images):
    """Save uploaded images and return list of file paths"""
    if not images:
        return []
    
    saved_paths = []
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    for image in images:
        if image and image.filename and allowed_file(image.filename):
            # Generate unique filename
            filename = secure_filename(image.filename)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            
            filepath = os.path.join(upload_folder, unique_filename)
            
            try:
                # Open and process image
                with Image.open(image) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize image while maintaining aspect ratio
                    img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    
                    # Save compressed image
                    img.save(filepath, 'JPEG', quality=85, optimize=True)
                
                # Store relative path for database
                relative_path = f"static/uploads/{unique_filename}"
                saved_paths.append(relative_path)
                
            except Exception as e:
                current_app.logger.error(f"Error saving image {filename}: {str(e)}")
                continue
    
    return saved_paths

def cleanup_expired_listings():
    """Remove expired listings from database"""
    from models import Listing
    
    try:
        expired_listings = Listing.query.filter(
            Listing.expires_at <= datetime.utcnow()
        ).all()
        
        for listing in expired_listings:
            # Delete associated image files
            if listing.image_urls:
                for image_url in listing.images:
                    try:
                        if image_url.startswith('static/uploads/'):
                            filepath = os.path.join(current_app.root_path, image_url)
                            if os.path.exists(filepath):
                                os.remove(filepath)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting image {image_url}: {str(e)}")
            
            db.session.delete(listing)
        
        if expired_listings:
            db.session.commit()
            current_app.logger.info(f"Cleaned up {len(expired_listings)} expired listings")
    
    except Exception as e:
        current_app.logger.error(f"Error during cleanup: {str(e)}")
        db.session.rollback()

def format_price(price):
    """Format price in Indian currency"""
    if price >= 100000:
        return f"₹{price/100000:.1f}L"
    elif price >= 1000:
        return f"₹{price/1000:.1f}K"
    else:
        return f"₹{int(price)}"

def get_whatsapp_url(phone, message):
    """Generate WhatsApp contact URL"""
    if not phone:
        return None
    
    # Clean phone number
    clean_phone = ''.join(filter(str.isdigit, phone))
    if not clean_phone.startswith('91') and len(clean_phone) == 10:
        clean_phone = '91' + clean_phone
    
    # URL encode message
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    return f"https://wa.me/{clean_phone}?text={encoded_message}"
