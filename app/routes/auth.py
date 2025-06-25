from flask import Blueprint, render_template , redirect , request , url_for, flash, session
from app.extensions import db
from datetime import datetime
from app.models import User, Role , RoleType , UserStatus

auth_bp = Blueprint('auth' , __name__)

@auth_bp.route('/login.html')
def login():
    return render_template('/auth/login.html')


@auth_bp.route('/signup.html')
def signup():
    return render_template('/auth/signup.html')


@auth_bp.route('/logout.html')
def logout():
    return redirect(url_for('main.index'))
