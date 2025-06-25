from flask import Blueprint, render_template, request
from app.models import User, Role

main_bp = Blueprint("main" , __name__)

@main_bp.route('/')
def index():
    # Home page
    return render_template('home.html')