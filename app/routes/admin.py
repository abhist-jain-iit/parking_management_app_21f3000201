from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime, timedelta
from app.models import *
import json
from app.decorators import require_permission
from sqlalchemy import func, or_
from decimal import Decimal
from functools import wraps
from app.models.geography import City
from app.models.enums import SpotStatus, UserStatus, ParkingLotStatus
from sqlalchemy.exc import IntegrityError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def refresh_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db.session.expire_all()  # clears SQLAlchemy cache
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard')
@require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def admin_dashboard():

    # Main admin dashboard with overview statistics.
    try:
        # Use this dummy reservation to test that everything is working fine.
        # dummy_reservation = Reservation(
        #     vehicle_number="TEST123",
        #     status=ReservationStatus.COMPLETED,
        #     user_id = 2,  # Or any valid non-CANCELLED status
        #     total_cost=Decimal("10.00"),
        #     start_time=datetime.utcnow(),
        #     end_time=datetime.utcnow() + timedelta(hours=2),
        #     parking_spot_id = 3,
        #     created_at=datetime.utcnow()
        # )

        # db.session.add(dummy_reservation)
        # db.session.commit()
        # Date reference
        today = datetime.now().date()
        
        # Reservation revenue
        today_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            func.date(Reservation.created_at) == today,
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0

        total_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0

        today_reservations = Reservation.query.filter(
            func.date(Reservation.created_at) == today
        ).count()

        # Recent activity
        recent_reservations = Reservation.query.order_by(
            Reservation.created_at.desc()
        ).limit(10).all()

        # Geographic stats
        total_continents = Continent.query.count()
        total_countries = Country.query.count()
        total_states = State.query.count()
        total_cities = City.query.count()

        # User & parking stats
        total_users = User.query.filter(User.username != 'admin').count()
        total_parking_lots = ParkingLot.query.count()
        total_parking_spots = ParkingSpot.query.count()
        total_reservations = Reservation.query.count()

        available_spots = ParkingSpot.count_available()
        reserved_spots = ParkingSpot.count_reserved()
        occupied_spots = ParkingSpot.count_occupied()

        # Dashboard statistics dictionary
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
            'occupancy_rate': round((occupied_spots / total_parking_spots * 100), 2)
                              if total_parking_spots > 0 else 0
        }

        # Provide latest 5 for dashboard quick management
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
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboards/admin_dashboard.html',
                               stats={},
                               recent_reservations=[])


# Result i got on testing which is correct hence test passed.
# {
#     "recent_reservations": [],
#     "stats": {
#         "available_spots": 350,
#         "occupancy_rate": 0,
#         "occupied_spots": 0,
#         "reserved_spots": 0,
#         "today_reservations": 0,
#         "today_revenue": 0,
#         "total_cities": 2,
#         "total_continents": 1,
#         "total_countries": 1,
#         "total_parking_lots": 3,
#         "total_parking_spots": 350,
#         "total_reservations": 0,
#         "total_revenue": 0,
#         "total_states": 3,
#         "total_users": 1
#     }
# }

@admin_bp.route('/users')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def manage_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    show_all = request.args.get('show_all', 0, type=int)
    query = User.query.filter(User.username != 'admin')
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
    if show_all:
        users = query.order_by(User.created_at.desc()).paginate(page=1, per_page=10000, error_out=False)
    else:
        users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users/manage.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def view_user_details(user_id):
    user = User.query.get_or_404(user_id)
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    return render_template('admin/users/details.html', user=user, reservations=reservations)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        data = request.form
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
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
        lot.name = data.get('name', lot.name)
        lot.address = data.get('address', lot.address)
        lot.city_id = int(data.get('city_id', lot.city_id))
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
    occupied = ParkingSpot.query.filter_by(parking_lot_id=lot.id, status='occupied').count()
    reserved = ParkingSpot.query.filter_by(parking_lot_id=lot.id, status='reserved').count()
    if occupied > 0 or reserved > 0:
        flash('Cannot delete lot with occupied or reserved spots!', 'danger')
        return redirect(url_for('admin.view_parking_lot_details', lot_id=lot.id))
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
        status_str = data.get('status', spot.status)
        if isinstance(status_str, str):
            spot.status = SpotStatus[status_str.upper()]
        else:
            spot.status = status_str
        db.session.commit()
        flash('Spot updated!', 'success')
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
        
        # Get spot revenue
        spot_revenue = db.session.query(func.sum(Reservation.total_cost)).filter_by(
            parking_spot_id=spot.id
        ).filter(
            Reservation.status != ReservationStatus.CANCELLED
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
            flash(error_msg, 'error')
            return redirect(url_for('admin.manage_parking_spots'))
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
                flash(error_msg, 'error')
                return redirect(url_for('admin.manage_parking_spots'))
        # Update status
        old_status = parking_spot.status
        parking_spot.status = new_status
        parking_spot.updated_at = datetime.utcnow()
        db.session.commit()
        success_msg = f'Parking spot "{parking_spot.spot_number}" status updated from {old_status} to {new_status}.'
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': success_msg,
                'parking_spot': {
                    'id': parking_spot.id,
                    'spot_number': parking_spot.spot_number,
                    'status': parking_spot.status,
                    'old_status': old_status
                }
            })
        flash(success_msg, 'success')
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error updating parking spot status: {str(e)}'
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'error')
    return redirect(url_for('admin.manage_parking_spots'))

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
        parent_id = int(data.get('parent_id')) if data.get('parent_id') else None
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
            return redirect(url_for('admin.manage_geography'))
        db.session.add(obj)
        db.session.commit()
        flash(f'{entity.capitalize()} created!', 'success')
        return redirect(url_for('admin.manage_geography'))
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
        obj.name = data.get('name', obj.name)
        if hasattr(obj, 'code'):
            obj.code = data.get('code', obj.code)
        if entity == 'country':
            obj.continent_id = data.get('parent_id', obj.continent_id)
        if entity == 'state':
            obj.country_id = data.get('parent_id', obj.country_id)
        if entity == 'city':
            obj.state_id = data.get('parent_id', obj.state_id)
            obj.pin_code = data.get('pin_code', obj.pin_code)
        db.session.commit()
        flash(f'{entity.capitalize()} updated!', 'success')
        return redirect(url_for('admin.manage_geography'))
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
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0
        total_revenue = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.status != ReservationStatus.CANCELLED
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
        total_parking_spots = ParkingSpot.query.count()
        total_reservations = Reservation.query.count()
        available_spots = ParkingSpot.count_available()
        reserved_spots = ParkingSpot.count_reserved()
        occupied_spots = ParkingSpot.count_occupied()
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
            'occupancy_rate': round((occupied_spots / total_parking_spots * 100), 2)
                              if total_parking_spots > 0 else 0
        }
        return render_template('admin/charts.html', stats=stats)
    except Exception as e:
        flash(f"Error loading charts: {str(e)}", "error")
        return render_template('admin/charts.html', stats={})


