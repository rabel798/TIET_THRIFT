# Tiet Thrift Deployment Guide - Complete Setup

## Overview
This guide covers deploying your Flask application on Vercel with a free PostgreSQL database.

## Prerequisites
- GitHub account
- Vercel account (free)
- Neon account (free PostgreSQL hosting)

## Part 1: Database Setup (Free PostgreSQL)

### Step 1: Create Neon Database Account
1. Go to https://neon.tech/
2. Sign up with GitHub (free tier: 512MB storage, 1 database)
3. Create a new project named "tiet-thrift"
4. Note down your connection string (starts with postgresql://)

### Step 2: Update Google OAuth Settings
1. Go to https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add these redirect URIs:
   - `https://your-app-name.vercel.app/google_login/callback`
   - `https://your-domain.com/google_login/callback` (if using custom domain)

## Part 2: Prepare Application for Deployment

### Step 3: Create Production Configuration
Create a file named `wsgi.py`:
```python
from main import app

if __name__ == "__main__":
    app.run()
```

### Step 4: Update Database Configuration
Modify your `app.py` to handle production environment:
```python
# Replace the database configuration section with:
if os.environ.get('DATABASE_URL'):
    # Production database (Neon/Railway)
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Development database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tiet_thrift.db"
```

## Part 3: Deploy to Vercel

### Step 5: GitHub Repository Setup
1. Push your code to GitHub repository
2. Ensure these files are in your root directory:
   - `vercel.json`
   - `main.py`
   - `app.py`
   - All your Python files

### Step 6: Vercel Deployment
1. Go to https://vercel.com/
2. Click "Import Project"
3. Connect your GitHub repository
4. Framework Preset: "Other"
5. Root Directory: leave blank
6. Build and Output Settings: leave default

### Step 7: Environment Variables Setup
In Vercel dashboard, go to Settings > Environment Variables and add:

```
DATABASE_URL=your_neon_connection_string
SESSION_SECRET=your_random_secret_key_here
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### Step 8: Deploy and Test
1. Click "Deploy"
2. Wait for deployment to complete
3. Test your application at the provided URL

## Alternative Free Backend Options

### Option 1: Railway (Recommended)
- Free tier: 512MB RAM, 1GB disk
- Built-in PostgreSQL
- Easy deployment

Steps:
1. Go to https://railway.app/
2. Connect GitHub repository
3. Add PostgreSQL service
4. Set environment variables
5. Deploy

### Option 2: Render
- Free tier: 512MB RAM, limited hours
- External database required

Steps:
1. Go to https://render.com/
2. Create web service from GitHub
3. Use Neon for database
4. Set environment variables

## Troubleshooting Common Issues

### Issue 1: Module Import Errors
Solution: Ensure all imports use relative paths and check file structure.

### Issue 2: Database Connection Errors
Solution: Verify DATABASE_URL format and Neon database is running.

### Issue 3: Static Files Not Loading
Solution: For Vercel, static files are served automatically from `/static` folder.

### Issue 4: Google OAuth Redirect Errors
Solution: Update redirect URIs in Google Console to match your deployed URL.

## Production Checklist

✅ Database connection string updated
✅ Environment variables set
✅ Google OAuth redirect URIs updated
✅ Static files accessible
✅ All dependencies listed
✅ Error handling implemented
✅ Security settings configured

## Monitoring and Maintenance

### Database Management
- Use Neon dashboard to monitor database usage
- Set up automatic backups
- Monitor connection limits

### Application Monitoring
- Use Vercel analytics for performance monitoring
- Set up error logging
- Monitor function execution times

## Scaling Considerations

### When to Upgrade
- Database storage > 400MB
- High traffic requiring more compute
- Need for advanced features

### Migration Path
- Upgrade Neon plan for more database storage
- Consider Railway Pro for more compute resources
- Implement Redis for session storage at scale

This setup provides a completely free hosting solution suitable for student projects and small-scale applications.