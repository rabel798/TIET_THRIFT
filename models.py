from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from sqlalchemy import DateTime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship with listings
    listings = db.relationship('Listing', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def active_listings_count(self):
        return Listing.query.filter(
            Listing.user_id == self.id,
            Listing.expires_at > datetime.utcnow()
        ).count()

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quality = db.Column(db.String(20), nullable=False)  # Like New, Good, Fair, Poor
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(200))  # Comma-separated tags
    image_urls = db.Column(db.Text)  # Comma-separated image URLs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    expires_at = db.Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    
    def __repr__(self):
        return f'<Listing {self.title}>'
    
    @property
    def images(self):
        """Return list of image URLs"""
        if self.image_urls:
            return [url.strip() for url in self.image_urls.split(',') if url.strip()]
        return []
    
    @property
    def tag_list(self):
        """Return list of tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    @property
    def is_expired(self):
        """Check if listing has expired"""
        return self.expires_at <= datetime.utcnow()
    
    @property
    def days_remaining(self):
        """Calculate days remaining before expiration"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def whatsapp_message(self):
        """Generate pre-filled WhatsApp message"""
        message = f"Hi! I'm interested in your listing: {self.title}\n"
        message += f"Price: ₹{self.price}\n"
        message += f"Quality: {self.quality}\n\n"
        message += "Could you please share more details?"
        return message
