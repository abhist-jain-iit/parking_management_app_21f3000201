from flask import Blueprint, render_template, request, session, redirect, url_for
from app.models import User, Role

main_bp = Blueprint("main" , __name__)

@main_bp.route('/')
def index():
    # Home page or main page route.
    # Check if user is logged in and redirect to appropriate dashboard
    if 'user_id' in session:
        user_role = session.get('user_role')
        if user_role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif user_role == 'user':
            return redirect(url_for('user.user_dashboard'))
    
    return render_template('home.html')