from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify, current_app
from app.extensions import db
from datetime import datetime
from app.models import *
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity, get_jwt

auth_bp = Blueprint('auth', __name__)

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
    # Logout route that clears user session.
    if request.method == 'POST':
        # More secure - requires POST request
        session.clear()
        flash('You have been logged out successfully', 'info')
        return redirect(url_for('index'))
    else:
        # GET request - show logout confirmation or redirect
        return redirect(url_for('index'))