from flask import Blueprint, render_template , redirect , request , url_for, flash, session
from app.extensions import db
from datetime import datetime
from app.models import *

auth_bp = Blueprint('auth' , __name__) 

# Now here lets create the route for Login.

@auth_bp.route('/login.html' , methods=['GET', 'POST'])
def login():
    #  Lets keep a Common login for both admin and users
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if admin
        if username == 'admin':
            admin = User.query.filter_by(username = 'admin').first()
            if admin and admin.check_password(pasword):
                session['user_id'] = admin.id
                session['user_role'] = 'admin'
                session['username'] = admin.username
                flash("Congrats! You are logged in as Admin, Welcome!")
                return render_template('/dashboards/admin_dashboard.html')
        
        user = User.query.filter_by(username = username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_role'] = 'user'
            session['username'] = user.username
            flash(f"Congrats! You have successfully logged in as: {user.first_name}")
            return redirect(url_for('user_dashboard'))
    return render_template('/auth/login.html')


@auth_bp.route('/signup.html' , methods=['GET', 'POST'])
def signup():
    #  This route is for user registration.
    return render_template('/auth/signup.html')


@auth_bp.route('/logout.html')
def logout():
    return redirect(url_for('main.index'))
