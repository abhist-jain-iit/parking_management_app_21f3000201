from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime
from app.models import *
from app.decorators import require_permission
from sqlalchemy import func, or_
from decimal import Decimal
from functools import wraps
from app.models.geography import City
from app.models.enums import SpotStatus, UserStatus, ParkingLotStatus
from sqlalchemy.exc import IntegrityError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def refresh_db_session(func):
    """Refresh database session to clear cache - helps prevent stale data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db.session.expire_all()
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/dashboard')
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def admin_dashboard():
    """Admin dashboard - shows system overview, revenue, and statistics"""
    try:
        print("Admin Dashboard: Loading admin dashboard")
        today = datetime.now().date()
        
        # Calculate total money earned (including cancelled reservations since users pay for time used)
        today_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            func.date(Reservation.created_at) == today,
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED])
        ).scalar() or 0

        total_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED])
        ).scalar() or 0

        today_reservations = Reservation.query.filter(
            func.date(Reservation.created_at) == today
        ).count()

        print(f"Admin Dashboard: Today's revenue ₹{float(today_revenue):.2f}, total revenue ₹{float(total_revenue):.2f}")

        # Get recent parking activity
        recent_reservations = Reservation.query.order_by(
            Reservation.created_at.desc()
        ).limit(10).all()

        # Count all the geography data (continents, countries, states, cities)
        total_continents = Continent.query.count()
        total_countries = Country.query.count()
        total_states = State.query.count()
        total_cities = City.query.count()

        # Count users and parking data
        total_users = User.query.filter(User.username != 'admin').count()
        total_parking_lots = ParkingLot.query.count()
        total_parking_spots = ParkingSpot.query.filter_by(is_deleted=False).count()
        total_reservations = Reservation.query.count()

        # Count parking spot statuses (available, reserved, occupied)
        available_spots = ParkingSpot.count_available()
        reserved_spots = ParkingSpot.count_reserved()
        occupied_spots = ParkingSpot.count_occupied()

        # Calculate how full the parking system is (occupied + reserved)
        occupancy_count = occupied_spots + reserved_spots
        occupancy_rate = round((occupancy_count / total_parking_spots * 100), 2) if total_parking_spots > 0 else 0

        # Dashboard statistics for display
        stats = {
            'total_continents': total_continents,
            'total_countries': total_countries,
            'total_states': total_states,
            'total_cities': total_cities,
            'total_users': total_users,
            'total_parking_lots': total_parking_lots,
            'total_parking_spots': total_parking_spots,
            'total_reservations': total_reservations,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots,
            'reserved_spots': reserved_spots,
            'today_reservations': today_reservations,
            'today_revenue': float(today_revenue),
            'total_revenue': float(total_revenue),
            'occupancy_rate': occupancy_rate
        }

        print(f"Admin Dashboard: System has {total_users} users, {total_parking_lots} lots, {total_parking_spots} spots, {occupancy_rate}% occupancy")

        # Get latest items for quick management
        users = User.query.filter(User.username != 'admin').order_by(User.created_at.desc()).limit(5).all()
        lots = ParkingLot.query.order_by(ParkingLot.created_at.desc()).limit(5).all()
        spots = ParkingSpot.query.order_by(ParkingSpot.created_at.desc()).limit(5).all()
        continents = Continent.query.order_by(Continent.created_at.desc()).limit(5).all()
        countries = Country.query.order_by(Country.created_at.desc()).limit(5).all()
        states = State.query.order_by(State.created_at.desc()).limit(5).all()
        cities = City.query.order_by(City.created_at.desc()).limit(5).all()

        return render_template('dashboards/admin_dashboard.html',
                               stats=stats,
                               recent_reservations=recent_reservations,
                               users=users,
                               lots=lots,
                               spots=spots,
                               continents=continents,
                               countries=countries,
                               states=states,
                               cities=cities)

    except Exception as e:
        print(f"Admin Dashboard Error: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboards/admin_dashboard.html',
                               stats={},
                               recent_reservations=[])

@admin_bp.route('/recent-reservations')
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def recent_reservations():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = Reservation.query.order_by(Reservation.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reservations = pagination.items
    return render_template('admin/recent_reservations.html', reservations=reservations, pagination=pagination)

@admin_bp.route('/users')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def manage_users():
    """Manage users - view, search, and manage user accounts"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    show_all = request.args.get('show_all', 0, type=int)
    
    print(f"Manage Users: Page {page}, search='{search}', show_all={show_all}")
    
    # Start with all users except admin
    query = User.query.filter(User.username != 'admin')
    
    # Search by username, email, first name, or last name
    if search:
        search_lower = search.lower()
        query = query.filter(
            or_(
                func.lower(User.username).contains(search_lower),
                func.lower(User.email).contains(search_lower),
                func.lower(User.first_name).contains(search_lower),
                func.lower(User.last_name).contains(search_lower)
            )
        )
    
    # Show all users or paginate
    if show_all:
        users = query.order_by(User.created_at.desc()).paginate(page=1, per_page=10000, error_out=False)
    else:
        users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    print(f"Manage Users: Found {users.total} users")
    return render_template('admin/users/manage.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def view_user_details(user_id):
    """View detailed information about a specific user and their parking history"""
    print(f"View User Details: Loading details for user {user_id}")
    user = User.query.get_or_404(user_id)
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    print(f"View User Details: Found {len(reservations)} reservations for user {user_id}")
    return render_template('admin/users/details.html', user=user, reservations=reservations)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def edit_user(user_id):
    """Edit user information (username, email, name)"""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        print(f"Edit User: Updating user {user_id}")
        data = request.form
        new_username = data.get('username', user.username)
        new_email = data.get('email', user.email)
        new_phone = data.get('phone', user.phone) if hasattr(user, 'phone') else None
        new_first_name = data.get('first_name', user.first_name)
        new_last_name = data.get('last_name', user.last_name)
        # Check for duplicate email (excluding current user)
        if User.query.filter(User.email == new_email, User.id != user.id).first():
            flash('A user with this email already exists. Please use a different email.', 'danger')
            return render_template('admin/users/edit.html', user=user)
        # Check for duplicate phone (excluding current user)
        if new_phone and User.query.filter(User.phone == new_phone, User.id != user.id).first():
            flash('A user with this phone number already exists. Please use a different phone number.', 'danger')
            return render_template('admin/users/edit.html', user=user)
        user.username = new_username
        user.email = new_email
        if new_phone:
            user.phone = new_phone
        user.first_name = new_first_name
        user.last_name = new_last_name
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.view_user_details', user_id=user_id))
    return render_template('admin/users/edit.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def change_user_status(user_id):
    user = User.query.get_or_404(user_id)
    new_status = request.form.get('new_status')
    if new_status not in [s.value for s in UserStatus]:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.manage_users'))
    user.status = UserStatus(new_status)
    db.session.commit()
    flash(f'User status changed to {new_status.title()}!', 'success')
    return redirect(url_for('admin.manage_users'))

# PARKING LOT ROUTES

@admin_bp.route('/lots')
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def list_lots():
    lots = ParkingLot.query.all()
    return render_template('admin/parking/lots.html', lots=lots)

@admin_bp.route('/lots/create', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def create_parking_lot():
    if request.method == 'POST':
        data = request.form
        name = data.get('name')
        address = data.get('address')
        city_id = int(data.get('city_id'))
        price_per_hour = float(data.get('price_per_hour', 0))
        total_spots = int(data.get('total_spots', 0))
        # Check for duplicate lot with same name, city, and address
        if ParkingLot.query.filter_by(name=name, city_id=city_id, address=address).first():
            flash('A parking lot with this name, address, and city already exists. Please choose another.', 'danger')
            return redirect(url_for('admin.create_parking_lot'))
        lot = ParkingLot(
            name=name,
            address=address,
            city_id=city_id,
            total_spots=total_spots,
            available_spots=total_spots,
            price_per_hour=price_per_hour
        )
        db.session.add(lot)
        db.session.flush()
        for i in range(1, total_spots + 1):
            spot = ParkingSpot(spot_number=f"{name}-{i:03d}", parking_lot_id=lot.id, status=SpotStatus.AVAILABLE)
            db.session.add(spot)
        db.session.commit()
        flash('Parking lot created!', 'success')
        return redirect(url_for('admin.list_lots'))
    cities = City.query.all()
    return render_template('admin/parking/create_lot.html', cities=cities)

@admin_bp.route('/lots/<int:lot_id>')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_parking_lot_details(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot.id).all()
    return render_template('admin/parking/lot_details.html', lot=lot, spots=spots)

@admin_bp.route('/lots/<int:lot_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        data = request.form
        new_name = data.get('name', lot.name)
        new_address = data.get('address', lot.address)
        new_city_id = int(data.get('city_id', lot.city_id))
        # Check for duplicate lot with same name, city, and address (excluding current lot)
        if ParkingLot.query.filter(ParkingLot.name == new_name, ParkingLot.city_id == new_city_id, ParkingLot.address == new_address, ParkingLot.id != lot.id).first():
            flash('A parking lot with this name, address, and city already exists. Please choose another.', 'danger')
            return redirect(url_for('admin.edit_parking_lot', lot_id=lot.id))
        lot.name = new_name
        lot.address = new_address
        lot.city_id = new_city_id
        lot.total_spots = int(data.get('total_spots', lot.total_spots))
        lot.price_per_hour = float(data.get('price_per_hour', lot.price_per_hour))
        status_str = data.get('status', lot.status)
        if isinstance(status_str, str):
            lot.status = ParkingLotStatus[status_str.upper()]
        else:
            lot.status = status_str
        db.session.commit()
        flash('Parking lot updated!', 'success')
        return redirect(url_for('admin.view_parking_lot_details', lot_id=lot.id))
    cities = City.query.all()
    return render_template('admin/parking/edit_lot.html', lot=lot, cities=cities)

@admin_bp.route('/lots/<int:lot_id>/delete', methods=['POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    # Only block deletion if any spot is reserved or occupied and not deleted
    blocking_spots = ParkingSpot.query.filter(
        ParkingSpot.parking_lot_id == lot.id,
        ParkingSpot.is_deleted == False,
        ParkingSpot.status.in_([SpotStatus.OCCUPIED.value, SpotStatus.RESERVED.value])
    ).all()
    if blocking_spots:
        print(f"[DEBUG] Cannot delete lot {lot.id}. Blocking spots: {[s.id for s in blocking_spots]}")
        flash('Cannot delete lot with reserved or occupied spots!', 'danger')
        return redirect(url_for('admin.view_parking_lot_details', lot_id=lot.id))
    # Delete all spots in this lot (hard delete)
    ParkingSpot.query.filter_by(parking_lot_id=lot.id).delete()
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted!', 'success')
    return redirect(url_for('admin.list_lots'))

@admin_bp.route('/parking/lots/search')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def search_parking_lots():
    # Advanced search for parking lots 
    search = request.args.get('search', '', type=str)
    location = request.args.get('location', '', type=str)
    min_spots = request.args.get('min_spots', 0, type=int)
    max_spots = request.args.get('max_spots', 0, type=int)
    status = request.args.get('status', '', type=str)  # available, full, partial
    
    query = ParkingLot.query
    
    if search:
        search_lower = search.lower()
        query = query.filter(or_(
            func.lower(ParkingLot.name).contains(search_lower),
            func.lower(ParkingLot.description).contains(search_lower)
        ))
    
    if location:
        query = query.filter(func.lower(ParkingLot.location).contains(location.lower()))
    
    if min_spots > 0:
        query = query.filter(ParkingLot.total_spots >= min_spots)
    
    if max_spots > 0:
        query = query.filter(ParkingLot.total_spots <= max_spots)
    
    parking_lots = query.all()
    
    # Filter by availability status if specified
    if status:
        filtered_lots = []
        for lot in parking_lots:
            available_spots = lot.parking_spots.filter_by(status='available').count()
            total_spots = lot.parking_spots.count()
            
            if status == 'available' and available_spots > 0:
                filtered_lots.append(lot)
            elif status == 'full' and available_spots == 0:
                filtered_lots.append(lot)
            elif status == 'partial' and 0 < available_spots < total_spots:
                filtered_lots.append(lot)
        
        parking_lots = filtered_lots
    
    # Prepare results with statistics
    results = []
    for lot in parking_lots:
        total_spots = lot.parking_spots.count()
        occupied = lot.parking_spots.filter_by(status='occupied').count()
        available = lot.parking_spots.filter_by(status='available').count()
        
        results.append({
            'lot': lot,
            'stats': {
                'total_spots': total_spots,
                'occupied': occupied,
                'available': available,
                'occupancy_rate': round((occupied / total_spots * 100), 2) if total_spots > 0 else 0
            }
        })
    
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        results_json = []
        for result in results:
            lot_dict = {
                'id': result['lot'].id,
                'name': result['lot'].name,
                'location': result['lot'].location,
                'description': result['lot'].description,
                'total_spots': result['lot'].total_spots
            }
            lot_dict.update(result['stats'])
            results_json.append(lot_dict)
        
        return jsonify({
            'success': True,
            'results': results_json,
            'search_params': {
                'search': search,
                'location': location,
                'min_spots': min_spots,
                'max_spots': max_spots,
                'status': status
            }
        })
    
    return render_template('admin/parking/search_lots.html', 
                          results=results,
                          search=search,
                          location=location,
                          min_spots=min_spots,
                          max_spots=max_spots,
                          status=status)

# PARKING SPOT ROUTES

@admin_bp.route('/spots')
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def list_spots():
    spots = ParkingSpot.query.all()
    return render_template('admin/parking/spots.html', spots=spots)

@admin_bp.route('/spots/<int:spot_id>')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_parking_spot_details(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    reservations = Reservation.query.filter_by(parking_spot_id=spot_id).order_by(Reservation.created_at.desc()).all()
    return render_template('admin/parking/spot_details.html', spot=spot, reservations=reservations)

@admin_bp.route('/spots/<int:spot_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def edit_parking_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if request.method == 'POST':
        data = request.form
        new_spot_number = data.get('spot_number', spot.spot_number)
        spot.spot_number = new_spot_number
        db.session.commit()
        flash('Spot number updated!', 'success')
        return redirect(url_for('admin.view_parking_spot_details', spot_id=spot.id))
    return render_template('admin/parking/edit_spot.html', spot=spot)

@admin_bp.route('/spots/<int:spot_id>/delete', methods=['POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def delete_parking_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status in ['occupied', 'reserved']:
        flash('Cannot delete occupied or reserved spot!', 'danger')
        return redirect(url_for('admin.view_parking_spot_details', spot_id=spot.id))
    db.session.delete(spot)
    db.session.commit()
    flash('Spot deleted!', 'success')
    return redirect(url_for('admin.list_spots'))

@admin_bp.route('/parking/spots/search')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def search_parking_spots():
    #  Advanced search for parking spots 
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    lot_id = request.args.get('lot_id', 0, type=int)
    availability = request.args.get('availability', '', type=str)  # available, occupied, reserved, under_maintenance, banned
    query = ParkingSpot.query
    if search:
        query = query.filter(func.lower(ParkingSpot.spot_number).contains(search.lower()))
    if status:
        query = query.filter_by(status=status)
    if lot_id > 0:
        query = query.filter_by(parking_lot_id=lot_id)
    if availability:
        query = query.filter_by(status=availability)
    parking_spots = query.all()
    
    # Prepare results with statistics
    results = []
    for spot in parking_spots:
        # Get current reservation if exists
        current_reservation = None
        if spot.status in ['occupied', 'reserved']:
            current_reservation = Reservation.query.filter_by(
                parking_spot_id=spot.id,
                status=ReservationStatus.ACTIVE
            ).first()
        
        # Get spot revenue - include cancelled reservations since users pay for time used
        spot_revenue = db.session.query(func.sum(Reservation.total_cost)).filter_by(
            parking_spot_id=spot.id
        ).filter(
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED])
        ).scalar() or 0
        
        results.append({
            'spot': spot,
            'stats': {
                'total_reservations': Reservation.query.filter_by(parking_spot_id=spot.id).count(),
                'revenue': float(spot_revenue),
                'current_reservation': {
                    'id': current_reservation.id,
                    'user_name': current_reservation.user.name if current_reservation and current_reservation.user else None,
                    'start_time': current_reservation.start_time.isoformat() if current_reservation else None,
                    'end_time': current_reservation.end_time.isoformat() if current_reservation else None
                } if current_reservation else None
            }
        })
    
    # Get all parking lots for filter dropdown
    parking_lots = ParkingLot.query.all()
    
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        results_json = []
        for result in results:
            spot_dict = {
                'id': result['spot'].id,
                'spot_number': result['spot'].spot_number,
                'status': result['spot'].status,
                'parking_lot_id': result['spot'].parking_lot_id,
                'parking_lot_name': result['spot'].parking_lot.name if result['spot'].parking_lot else None
            }
            spot_dict.update(result['stats'])
            results_json.append(spot_dict)
        
        return jsonify({
            'success': True,
            'results': results_json,
            'parking_lots': [{'id': lot.id, 'name': lot.name} for lot in parking_lots],
            'search_params': {
                'search': search,
                'status': status,
                'lot_id': lot_id,
                'availability': availability
            }
        })
    
    return render_template('admin/parking/search_spots.html',
                          results=results,
                          parking_lots=parking_lots,
                          search=search,
                          status=status,
                          lot_id=lot_id,
                          availability=availability)

@admin_bp.route('/spots/search')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def search_spots():
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    lot_id = request.args.get('lot_id', 0, type=int)
    query = ParkingSpot.query
    if search:
        query = query.filter(ParkingSpot.spot_number.ilike(f"%{search}%"))
    if status:
        query = query.filter_by(status=status)
    if lot_id > 0:
        query = query.filter_by(parking_lot_id=lot_id)
    spots = query.all()
    return render_template('admin/parking/spots.html', spots=spots, search=search, status=status, lot_id=lot_id)

@admin_bp.route('/parking/spots/<int:spot_id>/update-status', methods=['POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def update_spot_status(spot_id):
    # Quick update parking spot status 
    try:
        parking_spot = ParkingSpot.query.get_or_404(spot_id)
        # Handle JSON requests
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
        new_status = data.get('status')
        valid_statuses = ['available', 'occupied', 'reserved', 'under_maintenance', 'banned']
        if new_status not in valid_statuses:
            error_msg = 'Invalid status provided.'
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(url_for('admin.view_parking_spot_details', spot_id=spot_id))
        # Check if spot can be changed to the new status
        if new_status == 'available' and parking_spot.status in ['occupied', 'reserved']:
            # Check for active reservations
            active_reservations = Reservation.query.filter_by(
                parking_spot_id=spot_id,
                status=ReservationStatus.ACTIVE
            ).count()
            if active_reservations > 0:
                error_msg = 'Cannot set spot to available. It has active reservations.'
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'danger')
                return redirect(url_for('admin.view_parking_spot_details', spot_id=spot_id))
        # Update status
        old_status = parking_spot.status
        parking_spot.status = SpotStatus[new_status.upper()]
        parking_spot.updated_at = datetime.utcnow()
        db.session.commit()
        # Only flash a single success message
        flash('Parking spot status updated successfully.', 'success')
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Parking spot status updated successfully.',
                'parking_spot': {
                    'id': parking_spot.id,
                    'spot_number': parking_spot.spot_number,
                    'status': parking_spot.status.value,
                    'old_status': old_status.value if hasattr(old_status, "value") else old_status
                }
            })
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error updating parking spot status: {str(e)}'
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'danger')
    return redirect(url_for('admin.view_parking_spot_details', spot_id=spot_id))

# --- Geography Management (Admin CRUD) ---
@admin_bp.route('/geography', methods=['GET'])
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def manage_geography():
    continents = Continent.query.all()
    countries = Country.query.all()
    states = State.query.all()
    cities = City.query.all()
    return render_template('admin/geography/manage.html', continents=continents, countries=countries, states=states, cities=cities)

@admin_bp.route('/geography/create', methods=['GET', 'POST'])
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def create_geography():
    if request.method == 'POST':
        data = request.form
        entity = data.get('entity')
        name = data.get('name')
        code = data.get('code')
        parent_id = data.get('parent_id')
        pin_code = data.get('pin_code')

        # Debug: Print form data
        print(f"[DEBUG] Geography creation POST data: entity={entity}, name={name}, code={code}, parent_id={parent_id}, pin_code={pin_code}")

        # Validation
        if not entity:
            flash('Entity type is required!', 'danger')
            return redirect(url_for('admin.create_geography'))
        if not name:
            flash('Name is required!', 'danger')
            return redirect(url_for('admin.create_geography'))
        if entity in ['continent', 'country', 'state'] and not code:
            flash('Code is required!', 'danger')
            return redirect(url_for('admin.create_geography'))
        if entity in ['country', 'state', 'city']:
            if not parent_id or parent_id == 'None':
                flash('Parent selection is required!', 'danger')
                return redirect(url_for('admin.create_geography'))
            try:
                parent_id = int(parent_id)
            except Exception:
                flash('Invalid parent selection!', 'danger')
                return redirect(url_for('admin.create_geography'))

        try:
            # Pre-check for duplicates
            if entity == 'continent':
                # Check for exact duplicate
                if Continent.query.filter_by(name=name, code=code, status=GeographyStatus.ACTIVE).first():
                    flash('An identical continent already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if Continent.query.filter_by(name=name).first():
                    flash('A continent with this name already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if Continent.query.filter_by(code=code).first():
                    flash('A continent with this code already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                obj = Continent(name=name, code=code, status=GeographyStatus.ACTIVE)
            elif entity == 'country':
                # Check for exact duplicate
                if Country.query.filter_by(name=name, code=code, continent_id=parent_id, status=GeographyStatus.ACTIVE).first():
                    flash('An identical country already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if Country.query.filter_by(name=name, continent_id=parent_id).first():
                    flash('A country with this name already exists in the selected continent.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if Country.query.filter_by(code=code).first():
                    flash('A country with this code already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                obj = Country(name=name, code=code, continent_id=parent_id, status=GeographyStatus.ACTIVE)
            elif entity == 'state':
                # Check for exact duplicate
                if State.query.filter_by(name=name, code=code, country_id=parent_id, status=GeographyStatus.ACTIVE).first():
                    flash('An identical state already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if State.query.filter_by(name=name, country_id=parent_id).first():
                    flash('A state with this name already exists in the selected country.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if State.query.filter_by(code=code, country_id=parent_id).first():
                    flash('A state with this code already exists in the selected country.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                obj = State(name=name, code=code, country_id=parent_id, status=GeographyStatus.ACTIVE)
            elif entity == 'city':
                # Check for exact duplicate
                if City.query.filter_by(name=name, code=code, state_id=parent_id, pin_code=pin_code, status=GeographyStatus.ACTIVE).first():
                    flash('An identical city already exists.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if City.query.filter_by(code=code).first():
                    flash('A city with this code already exists. Please try another code.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if pin_code and City.query.filter_by(pin_code=pin_code).first():
                    flash('A city with this pin code already exists. Please try another pin code.', 'danger')
                    return redirect(url_for('admin.create_geography'))
                if not pin_code:
                    pin_code = None
                obj = City(name=name, code=code, state_id=parent_id, pin_code=pin_code, status=GeographyStatus.ACTIVE)
            else:
                flash('Invalid entity!', 'danger')
                return redirect(url_for('admin.create_geography'))
            db.session.add(obj)
            db.session.commit()
            flash(f'{entity.capitalize()} created!', 'success')
            return redirect(url_for('admin.manage_geography'))
        except IntegrityError as e:
            db.session.rollback()
            flash('A record with this name or code already exists. Please use a different value.', 'danger')
            return redirect(url_for('admin.create_geography'))
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"[ERROR] Exception during geography creation: {e}")
            traceback.print_exc()
            flash(f'Error creating {entity}: {str(e)}', 'danger')
            return redirect(url_for('admin.create_geography'))
    continents = Continent.query.all()
    countries = Country.query.all()
    states = State.query.all()
    return render_template('admin/geography/create.html', continents=continents, countries=countries, states=states)

@admin_bp.route('/geography/<entity>/<int:entity_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def edit_geography(entity, entity_id):
    model_map = {'continent': Continent, 'country': Country, 'state': State, 'city': City}
    obj = model_map[entity].query.get_or_404(entity_id)
    if request.method == 'POST':
        data = request.form
        new_name = data.get('name', obj.name)
        new_code = data.get('code', obj.code) if hasattr(obj, 'code') else None
        new_parent_id = data.get('parent_id')
        new_pin_code = data.get('pin_code', obj.pin_code) if entity == 'city' else None

        # Duplicate checks
        if entity == 'continent':
            duplicate_all = Continent.query.filter(Continent.name == new_name, Continent.code == new_code, Continent.status == GeographyStatus.ACTIVE, Continent.id != obj.id).first()
            if duplicate_all:
                flash('An identical continent already exists.', 'danger')
                return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())
        elif entity == 'country':
            parent_id = int(new_parent_id)
            duplicate_all = Country.query.filter(Country.name == new_name, Country.code == new_code, Country.continent_id == parent_id, Country.status == GeographyStatus.ACTIVE, Country.id != obj.id).first()
            if duplicate_all:
                flash('An identical country already exists.', 'danger')
                return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())
        elif entity == 'state':
            parent_id = new_parent_id or obj.country_id
            duplicate_all = State.query.filter(State.name == new_name, State.code == new_code, State.country_id == parent_id, State.status == GeographyStatus.ACTIVE, State.id != obj.id).first()
            if duplicate_all:
                flash('An identical state already exists.', 'danger')
                return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())
        elif entity == 'city':
            parent_id = new_parent_id or obj.state_id
            duplicate_all = City.query.filter(City.name == new_name, City.code == new_code, City.state_id == parent_id, City.pin_code == new_pin_code, City.status == GeographyStatus.ACTIVE, City.id != obj.id).first()
            if duplicate_all:
                flash('An identical city already exists.', 'danger')
                return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())

        # If no duplicates, update the object
        obj.name = new_name
        if hasattr(obj, 'code'):
            obj.code = new_code
        if entity == 'country':
            obj.continent_id = int(new_parent_id) if new_parent_id else obj.continent_id
        if entity == 'state':
            obj.country_id = new_parent_id or obj.country_id
        if entity == 'city':
            obj.state_id = new_parent_id or obj.state_id
            obj.pin_code = new_pin_code
        try:
            db.session.commit()
            flash(f'{entity.capitalize()} updated!', 'success')
            return redirect(url_for('admin.manage_geography'))
        except IntegrityError as e:
            db.session.rollback()
            flash('A record with this name or code already exists. Please use a different value.', 'danger')
            return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating {entity}: {str(e)}', 'danger')
            return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=Continent.query.all(), countries=Country.query.all(), states=State.query.all())
    continents = Continent.query.all()
    countries = Country.query.all()
    states = State.query.all()
    return render_template('admin/geography/edit.html', entity=entity, obj=obj, continents=continents, countries=countries, states=states)

@admin_bp.route('/geography/<entity>/<int:entity_id>/delete', methods=['POST'])
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def delete_geography(entity, entity_id):
    model_map = {'continent': Continent, 'country': Country, 'state': State, 'city': City}
    obj = model_map[entity].query.get_or_404(entity_id)
    try:
        # No need to check for lots in city; cascade will handle deletion
        db.session.delete(obj)
        db.session.commit()
        flash(f'{entity.capitalize()} deleted!', 'success')
    except IntegrityError as e:
        db.session.rollback()
        flash(f'Cannot delete {entity}: it is still referenced by other records. Remove all children or dependencies first.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting {entity}: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_geography'))

# --- User-side Geography Creation Route ---
from flask import Blueprint as UserBlueprint
user_geo_bp = UserBlueprint('user_geo', __name__, url_prefix='/user-geo')

@user_geo_bp.route('/create', methods=['GET', 'POST'])
def user_create_geography():
    if request.method == 'POST':
        data = request.form
        entity = data.get('entity')
        name = data.get('name')
        code = data.get('code')
        parent_id = data.get('parent_id')
        if entity == 'continent':
            obj = Continent(name=name, code=code, status=GeographyStatus.ACTIVE)
        elif entity == 'country':
            obj = Country(name=name, code=code, continent_id=parent_id, status=GeographyStatus.ACTIVE)
        elif entity == 'state':
            obj = State(name=name, code=code, country_id=parent_id, status=GeographyStatus.ACTIVE)
        elif entity == 'city':
            obj = City(name=name, state_id=parent_id, pin_code=data.get('pin_code'), status=GeographyStatus.ACTIVE)
        else:
            flash('Invalid entity!', 'danger')
            return redirect(url_for('user_geo.user_create_geography'))
        db.session.add(obj)
        db.session.commit()
        flash(f'{entity.capitalize()} created!', 'success')
        return redirect(url_for('user_geo.user_create_geography'))
    continents = Continent.query.all()
    countries = Country.query.all()
    states = State.query.all()
    return render_template('user/geography/create.html', continents=continents, countries=countries, states=states)

# Register user_geo_bp in your app factory or __init__.py
# ... existing code ...

@admin_bp.route('/charts')
@require_permission(PermissionType.VIEW_ANALYTICS.value)
@refresh_db_session
def admin_charts():
    try:
        today = datetime.now().date()
        today_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            func.date(Reservation.created_at) == today,
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED])
        ).scalar() or 0
        total_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED])
        ).scalar() or 0
        today_reservations = Reservation.query.filter(
            func.date(Reservation.created_at) == today
        ).count()
        total_continents = Continent.query.count()
        total_countries = Country.query.count()
        total_states = State.query.count()
        total_cities = City.query.count()
        total_users = User.query.filter(User.username != 'admin').count()
        total_parking_lots = ParkingLot.query.count()
        total_parking_spots = ParkingSpot.query.filter_by(is_deleted=False).count()
        total_reservations = Reservation.query.count()
        available_spots = ParkingSpot.count_available()
        reserved_spots = ParkingSpot.count_reserved()
        occupied_spots = ParkingSpot.count_occupied()
        occupancy_count = reserved_spots + occupied_spots
        stats = {
            'total_continents': total_continents,
            'total_countries': total_countries,
            'total_states': total_states,
            'total_cities': total_cities,
            'total_users': total_users,
            'total_parking_lots': total_parking_lots,
            'total_parking_spots': total_parking_spots,
            'total_reservations': total_reservations,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots,
            'reserved_spots': reserved_spots,
            'today_reservations': today_reservations,
            'today_revenue': float(today_revenue),
            'total_revenue': float(total_revenue),
            'occupancy_rate': round((occupancy_count / total_parking_spots * 100), 2)
                              if total_parking_spots > 0 else 0
        }
        return render_template('admin/charts.html', stats=stats)
    except Exception as e:
        flash(f"Error loading charts: {str(e)}", "error")
        return render_template('admin/charts.html', stats={})




