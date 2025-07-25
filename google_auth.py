# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")}/google_login/callback'

# Get the current domain from environment
CURRENT_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")

# ALWAYS display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use the exact redirect URI that should be registered in Google Console
        redirect_uri = f"https://{CURRENT_DOMAIN}/google_login/callback"
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
            # Add additional parameters to bypass iframe restrictions
            hd="thapar.edu"  # Restrict to thapar.edu domain
        )
        return redirect(request_uri)
    except Exception as e:
        flash('Authentication service is currently unavailable. Please try again later.', 'error')
        return redirect(url_for('index'))


@google_auth.route("/google_login/callback")
def callback():
    try:
        code = request.args.get("code")
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Use the exact same redirect URI as in the login function
        redirect_uri = f"https://{CURRENT_DOMAIN}/google_login/callback"
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=redirect_uri,
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo["given_name"]
        else:
            flash("User email not available or not verified by Google.", 'error')
            return redirect(url_for('index'))

        # Check if email is from Thapar domain
        if not users_email.endswith('@thapar.edu'):
            flash('Access restricted to Thapar University students only. Please use your @thapar.edu email.', 'error')
            return redirect(url_for('index'))

        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User()
            user.username = users_name
            user.email = users_email
            db.session.add(user)
            db.session.commit()
            flash(f'Welcome to Tiet Thrift, {users_name}! Please complete your profile.', 'success')

        login_user(user)
        return redirect(url_for("dashboard"))
    
    except Exception as e:
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('index'))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for("index"))
