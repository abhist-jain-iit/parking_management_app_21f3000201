from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify, current_app
from app.extensions import db
from datetime import datetime
from app.models import *
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity, get_jwt
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
from flask_login import login_user

auth_bp = Blueprint('auth', __name__)

serializer = URLSafeTimedSerializer('super-secret-key')

# Now here lets create the route for Login.

@auth_bp.route('/login' , methods=['GET', 'POST'])
def login():
    # data = request.get_json() for postman checking
    # username = data.get('username')
    # return jsonify({'error': 'Username and password are required!'}), 400
    #  Lets keep a Common login for both admin and users
    # print(f"Request headers: {dict(request.headers)}")
    # print(f"Request content type: {request.content_type}")
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Username and password are required!'}), 400
            flash("Username and password are required!")
            return render_template('auth/login.html')

        # Check if admin
        if username == 'admin':
            admin = User.query.filter_by(username='admin').first()
            if admin and admin.check_password(password):
                login_user(admin)
                session['user_id'] = admin.id
                session['user_role'] = 'admin'
                session['username'] = admin.username
                
                if request.is_json:
                    return jsonify({
                        'message': 'Admin login successful',
                        'redirect': url_for('admin.admin_dashboard')
                    })
                
                flash("Welcome Admin! You are logged in successfully.")
                return redirect(url_for('admin.admin_dashboard'))
            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid admin credentials!'}), 401
                flash("Invalid admin credentials!")
                return render_template('auth/login.html')
        else:
            # Regular user login
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                if user.status in [UserStatus.INACTIVE, UserStatus.BANNED]:
                    msg = 'Your account is inactive or banned. Please contact support.'
                    if request.is_json:
                        return jsonify({'error': msg}), 403
                    flash(msg)
                    return render_template('auth/login.html')
                login_user(user)
                session['user_id'] = user.id
                session['user_role'] = 'user'
                session['username'] = user.username
                
                if request.is_json:
                    return jsonify({
                        'message': f'Login successful! Welcome {user.first_name}',
                        'redirect': url_for('main.index')  # Fixed: use main.index
                    })
                
                flash(f"Welcome {user.first_name}! You have successfully logged in.")
                return redirect(url_for('main.index'))  # Fixed: redirect to main page
            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid username or password!'}), 401
                flash("Invalid username or password!")
                return render_template('auth/login.html')
                
    return render_template('auth/login.html')
    


@auth_bp.route('/signup' , methods=['GET', 'POST'])
def signup():
    # data = request.get_json() for postman checking
    # username = data.get('username')
    # return jsonify({'error': 'Username and password are required!'}), 400
    #  Lets keep a Common login for both admin and users
    #  This route is for user registration.
    
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        gender = data.get('gender')
        confirm_password = data.get('confirm_password')
        
        # Validation errors list
        errors = []

        # Basic field validation
        if not first_name:
            errors.append("First name is required")
        if not last_name:
            errors.append("Last name is required")
        if not username:
            errors.append("Username is required")
        if not email:
            errors.append("Email is required")
        if not phone:
            errors.append("Phone number is required")
        if not password:
            errors.append("Password is required")
        if not confirm_password:
            errors.append("Password confirmation is required")

        # Password confirmation check
        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match")

        # Email validation using the model's static method
        if email and not User.validate_email(email):
            errors.append("Invalid email format")

        # Check for existing users
        if username and User.query.filter_by(username=username).first():
            errors.append("Username already exists")
        
        if email and User.query.filter_by(email=email).first():
            errors.append("Email already registered")

        # Gender validation
        if gender:
            try:
                gender_enum = GenderEnum(gender)
            except ValueError:
                errors.append("Invalid gender selection")
        else:
            gender_enum = GenderEnum.OTHER

        # If no errors so far, create user and validate password
        if not errors:
            try:
                # Create new user instance
                new_user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                    phone=phone,
                    gender=gender_enum,
                    status=UserStatus.ACTIVE  # Default status
                )
                
                # Set password (this will validate the password)
                new_user.set_password(password)
                
                # Add to database
                db.session.add(new_user)
                db.session.flush()  # Get new_user.id before commit
                # Assign default 'user' role (lowercase, as in DB)
                user_role = Role.query.filter_by(name='user').first()
                if user_role:
                    new_user_role = UserRole(user_id=new_user.id, role_id=user_role.id)
                    db.session.add(new_user_role)
                db.session.commit()
                
                # Success response
                if request.is_json:
                    return jsonify({
                        'message': 'Registration successful! You can now log in.',
                        'redirect': url_for('auth.login')
                    })

                # jsonify({"first_name" : "Abhist","last_name" : "Jain", "username" : "abhist","email" : "abhistjain@gmail.com","phone" : "+918303776445", "gender" : "male"})
                
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
                
            except ValueError as e:
                # Password validation error
                errors.append(str(e))
                db.session.rollback()
            except Exception as e:
                # Database or other errors
                errors.append("Registration failed. Please try again.")
                db.session.rollback()
                current_app.logger.error(f"Registration error: {str(e)}")

        # If there are errors, return them
        if errors:
            if request.is_json:
                return jsonify({'errors': errors}), 400
                
            for error in errors:
                flash(error, 'error')
            
            # Return form with preserved data (except passwords)
            return render_template('auth/signup.html', 
                                 first_name=first_name,
                                 last_name=last_name,
                                 username=username,
                                 email=email,
                                 phone=phone,
                                 gender=gender)
                                 
    return render_template('auth/signup.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username != 'admin':
            flash('Only the admin can log in here.', 'danger')
            return render_template('auth/admin_login.html')
        admin = User.query.filter_by(username='admin').first()
        if admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['user_role'] = 'admin'
            session['username'] = admin.username
            flash('Welcome Admin! You are logged in successfully.', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
            return render_template('auth/admin_login.html')
    return render_template('auth/admin_login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if not user:
            flash('No user found with that email or username.', 'danger')
            return render_template('auth/forgot_password.html')
        token = serializer.dumps(user.id)
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        flash(f'Password reset link (for demo): {reset_url}', 'info')
        # In production, send this link via email
        return render_template('auth/forgot_password.html')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = serializer.loads(token, max_age=3600)
    except Exception:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or not confirm_password:
            flash('Please fill out all fields.', 'danger')
            return render_template('auth/reset_password.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')
        try:
            user.set_password(password)
            db.session.commit()
            flash('Password reset successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Password reset failed. Please try again.', 'danger')
            return render_template('auth/reset_password.html')
    return render_template('auth/reset_password.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            flash('Please fill out all fields.', 'danger')
            return render_template('auth/change_password.html')
        if not user.check_password(old_password):
            flash('Old password is incorrect.', 'danger')
            return render_template('auth/change_password.html')
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')
        try:
            user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash('Password change failed. Please try again.', 'danger')
            return render_template('auth/change_password.html')
    return render_template('auth/change_password.html')