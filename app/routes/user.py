from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime
from app.models import *
from app.decorators import require_permission
from sqlalchemy import func
from decimal import Decimal
from app.models.enums import PermissionType, ParkingLotStatus, SpotStatus
from app.models.parking import ParkingSpot, Reservation
from app.models.geography import Country, State, City

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
def user_dashboard():
    """User dashboard - shows all user's parking reservations and statistics"""
    flash_msg = request.args.get('flash')
    if flash_msg:
        flash(flash_msg, 'success')
    
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to view your dashboard.', 'danger')
        return redirect(url_for('auth.login'))
    
    print(f"User Dashboard: Loading dashboard for user ID {user_id}")
    
    user = User.query.get(user_id)
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    
    # Sort reservations by status (active, completed, cancelled)
    active_reservations = [r for r in reservations if r.status == ReservationStatus.ACTIVE]
    completed_reservations = [r for r in reservations if r.status == ReservationStatus.COMPLETED]
    cancelled_reservations = [r for r in reservations if r.status == ReservationStatus.CANCELLED]
    
    print(f"User Dashboard: Found {len(active_reservations)} active, {len(completed_reservations)} completed, {len(cancelled_reservations)} cancelled reservations")
    
    # Calculate money statistics
    total_spent = sum(float(r.total_cost) for r in completed_reservations if r.total_cost)
    total_spent_including_cancelled = sum(float(r.total_cost) for r in completed_reservations + cancelled_reservations if r.total_cost)
    total_time = sum((r.end_time - r.start_time).total_seconds() / 3600 for r in completed_reservations if r.end_time and r.start_time)
    total_bookings = len(reservations)
    
    print(f"User Dashboard: Total spent ₹{total_spent:.2f}, including cancelled ₹{total_spent_including_cancelled:.2f}")
    
    # Calculate current bill for active reservations
    active_spending = 0
    now = datetime.utcnow()
    for r in active_reservations:
        if r.start_time:
            # Calculate how long they've been parked
            duration = (now - r.start_time).total_seconds() / 3600
            rate = float(r.parking_spot.parking_lot.price_per_hour) if r.parking_spot and r.parking_spot.parking_lot else 0
            r.estimated_cost = duration * rate
            active_spending += r.estimated_cost
        else:
            r.estimated_cost = 0
    
    print(f"User Dashboard: Current active spending ₹{active_spending:.2f}")
    
    lots = ParkingLot.query.all()
    spots = ParkingSpot.query.filter_by(status=SpotStatus.AVAILABLE).all()

    # Occupancy rate for user dashboard (same as admin)
    total_spots = ParkingSpot.query.filter_by(is_deleted=False).count()
    reserved_spots = ParkingSpot.count_reserved()
    occupied_spots = ParkingSpot.count_occupied()
    occupancy_count = reserved_spots + occupied_spots
    occupancy_rate = round((occupancy_count / total_spots * 100), 2) if total_spots > 0 else 0

    return render_template('dashboards/user_dashboard.html',
                           user=user,
                           active_reservations=active_reservations,
                           completed_reservations=completed_reservations,
                           cancelled_reservations=cancelled_reservations,
                           lots=lots,
                           spots=spots,
                           total_spent=total_spent,
                           total_spent_including_cancelled=total_spent_including_cancelled,
                           total_time=total_time,
                           total_bookings=total_bookings,
                           active_spending=active_spending,
                           now=datetime.utcnow(),
                           occupancy_rate=occupancy_rate
                           )

@user_bp.route('/search_lots', methods=['POST'])
def search_lots():
    """Search for parking lots by location (country, state, city)"""
    data = request.get_json() or request.form
    country_id = data.get('country')
    state_id = data.get('state')
    city_id = data.get('city')
    lot_name = data.get('lot_name', '').strip()
    page = int(data.get('page', 1))
    per_page = int(data.get('per_page', 10))

    print(f"Lot Search: Searching with country={country_id}, state={state_id}, city={city_id}, name='{lot_name}'")

    # Start with only active parking lots
    query = ParkingLot.query.filter(ParkingLot.status == ParkingLotStatus.ACTIVE)

    # Apply location filters (city, state, or country)
    if city_id:
        query = query.filter(ParkingLot.city_id == city_id)
    elif state_id:
        # Get all cities in this state
        city_ids = [c.id for c in City.query.filter_by(state_id=state_id).all()]
        if city_ids:
            query = query.filter(ParkingLot.city_id.in_(city_ids))
    elif country_id:
        # Get all states in this country, then all cities in those states
        state_ids = [s.id for s in State.query.filter_by(country_id=country_id).all()]
        city_ids = [c.id for c in City.query.filter(City.state_id.in_(state_ids)).all()]
        if city_ids:
            query = query.filter(ParkingLot.city_id.in_(city_ids))

    # Search by lot name if provided
    if lot_name:
        query = query.filter(ParkingLot.name.ilike(f"%{lot_name}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    lots = pagination.items

    print(f"Lot Search: Found {len(lots)} lots out of {pagination.total} total")

    result = []
    for lot in lots:
        city = City.query.get(lot.city_id)
        result.append({
            'id': lot.id,
            'name': lot.name,
            'address': lot.address,
            'city_name': city.name if city else '',
            'available_spots': lot.available_spots,
            'price_per_hour': float(lot.price_per_hour),
        })

    return jsonify({'lots': result, 'total': pagination.total, 'pages': pagination.pages, 'page': page})

@user_bp.route('/update_reservation_status', methods=['POST'])
def update_reservation_status():
    """Update reservation status - mark as occupied or release the spot"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    reservation_id = request.json.get('reservation_id')
    new_status = request.json.get('status')
    
    print(f"Reservation Status: User {user_id} updating reservation {reservation_id} to {new_status}")
    
    reservation = Reservation.query.get(reservation_id)
    if not reservation or reservation.user_id != user_id:
        return jsonify({'success': False, 'message': 'Reservation not found'}), 404
    
    spot = reservation.parking_spot
    lot = spot.parking_lot
    now = datetime.utcnow()
    
    try:
        if new_status == 'occupied':
            # Mark spot as occupied (car is parked)
            spot.status = SpotStatus.OCCUPIED
            db.session.commit()
            print(f"Reservation Status: Spot {spot.spot_number} marked as occupied")
            return jsonify({'success': True, 'message': 'Spot marked as occupied'})
            
        elif new_status == 'released':
            # Release the spot and calculate final bill
            spot.status = SpotStatus.AVAILABLE
            reservation.end_time = now
            
            # Calculate parking duration and cost
            duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
            rounded_hours = int(duration_hours) + (1 if duration_hours % 1 > 0 else 0)
            reservation.total_cost = rounded_hours * float(lot.price_per_hour)
            reservation.status = ReservationStatus.COMPLETED
            
            db.session.commit()
            lot.update_available_spots()
            
            print(f"Reservation Status: Spot {spot.spot_number} released, cost ₹{reservation.total_cost:.2f}")
            return jsonify({'success': True, 'message': 'Spot released', 'bill': reservation.total_cost})
            
        else:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Reservation Status Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to update status: {str(e)}'}), 500

@user_bp.route('/user_reservations', methods=['GET'])
def user_reservations():
    """Get user's complete reservation history"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    print(f"User Reservations: Loading history for user {user_id}")
    
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    data = []
    total_time = 0
    total_spent = 0
    
    for r in reservations:
        duration = 0
        if r.status == ReservationStatus.COMPLETED and r.end_time and r.start_time:
            duration = (r.end_time - r.start_time).total_seconds() / 3600
            total_time += duration
            total_spent += float(r.total_cost)
        data.append({
            'id': r.id,
            'lot': r.parking_spot.parking_lot.name if r.parking_spot and r.parking_spot.parking_lot else None,
            'spot': r.parking_spot.spot_number if r.parking_spot else None,
            'start_time': r.start_time.isoformat() if r.start_time else None,
            'end_time': r.end_time.isoformat() if r.end_time else None,
            'status': r.status.value,
            'total_cost': float(r.total_cost) if r.total_cost else 0,
            'duration_hours': duration
        })
    
    summary = {
        'total_bookings': len(reservations),
        'total_time': total_time,
        'total_spent': total_spent
    }
    
    print(f"User Reservations: Found {len(reservations)} reservations, total spent ₹{total_spent:.2f}")
    return jsonify({'reservations': data, 'summary': summary})

@user_bp.route('/user_reservations_paginated', methods=['GET'])
def user_reservations_paginated():
    """Get user reservations with pagination (for large lists)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    
    print(f"User Reservations Paginated: User {user_id}, status={status}, page={page}")
    
    query = Reservation.query.filter_by(user_id=user_id)
    if status:
        query = query.filter(Reservation.status == status)
    query = query.order_by(Reservation.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reservations = pagination.items
    data = []
    
    for r in reservations:
        duration = 0
        if r.status == ReservationStatus.COMPLETED and r.end_time and r.start_time:
            duration = (r.end_time - r.start_time).total_seconds() / 3600
        data.append({
            'id': r.id,
            'lot': r.parking_spot.parking_lot.name if r.parking_spot and r.parking_spot.parking_lot else None,
            'spot': r.parking_spot.spot_number if r.parking_spot else None,
            'start_time': r.start_time.strftime('%Y-%m-%d %H:%M') if r.start_time else None,
            'end_time': r.end_time.strftime('%Y-%m-%d %H:%M') if r.end_time else None,
            'status': r.status.value,
            'total_cost': float(r.total_cost) if r.total_cost else 0,
            'duration_hours': duration
        })
    
    return jsonify({
        'reservations': data,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })

@user_bp.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile information"""
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to edit your profile.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if request.method == 'POST':
        # Update user information from form
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        db.session.commit()
        
        print(f"Profile Update: User {user_id} updated their profile")
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.user_dashboard'))
    
    return render_template('user/edit_profile.html', user=user)

@user_bp.route('/get_continents', methods=['GET'])
def get_continents():
    """Get all continents for dropdown selection"""
    continents = Continent.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in continents])

@user_bp.route('/get_countries', methods=['GET'])
def get_countries():
    """Get countries by continent for dropdown selection"""
    continent_id = request.args.get('continent_id')
    query = Country.query
    if continent_id:
        query = query.filter_by(continent_id=continent_id)
    countries = query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in countries])

@user_bp.route('/get_states', methods=['GET'])
def get_states():
    """Get states by country for dropdown selection"""
    country_id = request.args.get('country_id')
    query = State.query
    if country_id:
        query = query.filter_by(country_id=country_id)
    states = query.all()
    return jsonify([{'id': s.id, 'name': s.name} for s in states])

@user_bp.route('/get_cities', methods=['GET'])
def get_cities():
    """Get cities by state for dropdown selection"""
    state_id = request.args.get('state_id')
    query = City.query
    if state_id:
        query = query.filter_by(state_id=state_id)
    cities = query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in cities])

@user_bp.route('/get_lots', methods=['GET'])
def get_lots():
    """Get parking lots by city for dropdown selection"""
    city_id = request.args.get('city_id')
    query = ParkingLot.query.filter_by(status=ParkingLotStatus.ACTIVE)
    if city_id:
        query = query.filter_by(city_id=city_id)
    lots = query.all()
    
    result = []
    for l in lots:
        city = City.query.get(l.city_id)
        result.append({
            'id': l.id,
            'name': l.name,
            'address': l.address,
            'available_spots': l.available_spots,
            'price_per_hour': float(l.price_per_hour),
            'city_name': city.name if city else ''
        })
    return jsonify(result)

@user_bp.route('/lot/<int:lot_id>')
def lot_details(lot_id):
    """Show detailed information about a specific parking lot"""
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot.id).all()
    spot_dicts = [s.to_dict() for s in spots]
    return render_template('user/lot_details.html', lot=lot, spots=spot_dicts)

@user_bp.route('/book-reservation')
def book_reservation():
    """Show the booking reservation page"""
    countries = Country.query.all()
    return render_template('user/book_reservation.html', countries=countries)

@user_bp.route('/api/states')
def api_get_states():
    """API endpoint: Get states by country ID"""
    country_id = request.args.get('country_id', type=int)
    states = State.query.filter_by(country_id=country_id).all() if country_id else []
    return jsonify([{'id': s.id, 'name': s.name} for s in states])

@user_bp.route('/api/cities')
def api_get_cities():
    """API endpoint: Get cities by state ID"""
    state_id = request.args.get('state_id', type=int)
    cities = City.query.filter_by(state_id=state_id).all() if state_id else []
    return jsonify([{'id': c.id, 'name': c.name} for c in cities])

@user_bp.route('/api/lots')
def api_get_lots():
    """API endpoint: Get parking lots with location filters"""
    country_id = request.args.get('country_id', type=int)
    state_id = request.args.get('state_id', type=int)
    city_id = request.args.get('city_id', type=int)
    
    query = ParkingLot.query
    if city_id:
        query = query.filter_by(city_id=city_id)
    elif state_id:
        city_ids = [c.id for c in City.query.filter_by(state_id=state_id).all()]
        query = query.filter(ParkingLot.city_id.in_(city_ids))
    elif country_id:
        state_ids = [s.id for s in State.query.filter_by(country_id=country_id).all()]
        city_ids = [c.id for c in City.query.filter(City.state_id.in_(state_ids)).all()]
        query = query.filter(ParkingLot.city_id.in_(city_ids))
    
    lots = query.all()
    result = []
    for lot in lots:
        city = City.query.get(lot.city_id)
        result.append({
            'id': lot.id,
            'name': lot.name,
            'address': lot.address,
            'price_per_hour': float(lot.price_per_hour),
            'available_spots': lot.available_spots,
            'city_name': city.name if city else ''
        })
    return jsonify(result)

@user_bp.route('/api/lot-spots/<int:lot_id>')
def api_lot_spots(lot_id):
    """API endpoint: Get all spots for a specific parking lot"""
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot_id).all()
    return jsonify([spot.to_dict() for spot in spots])

@user_bp.route('/book-spot/<int:spot_id>', methods=['POST'])
def book_spot(spot_id):
    """Book a specific parking spot"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    print(f"Book Spot: User {user_id} attempting to book spot {spot_id}")
    
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = spot.parking_lot
    
    # Check if parking lot is active and available
    if lot.status != ParkingLotStatus.ACTIVE:
        return jsonify({'success': False, 'message': f'Lot is {lot.status.value}'}), 400
    
    # Check if spot is available for booking
    if spot.status != SpotStatus.AVAILABLE:
        return jsonify({'success': False, 'message': f'Spot is {spot.status.value}'}), 400
    
    # Check if user already has an active reservation for this spot
    existing_reservation = Reservation.query.filter_by(
        user_id=user_id,
        parking_spot_id=spot_id,
        status=ReservationStatus.ACTIVE
    ).first()
    
    if existing_reservation:
        return jsonify({'success': False, 'message': 'You already have an active reservation for this spot'}), 400
    
    # Get vehicle number from request
    vehicle_number = request.json.get('vehicle_number')
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'Vehicle number is required'}), 400
    
    try:
        # Create new reservation
        reservation = Reservation(
            user_id=user_id,
            parking_spot_id=spot_id,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),  # Will be updated when vacated
            vehicle_number=vehicle_number,
            total_cost=0,
            status=ReservationStatus.ACTIVE
        )
        
        # Mark spot as reserved
        spot.status = SpotStatus.RESERVED
        
        db.session.add(reservation)
        db.session.commit()
        
        # Update available spots count in the lot
        lot.update_available_spots()
        
        print(f"Book Spot: Successfully booked spot {spot.spot_number} in lot {lot.name} for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Spot booked successfully',
            'reservation_id': reservation.id,
            'spot_number': spot.spot_number,
            'lot_name': lot.name,
            'vehicle_number': vehicle_number,
            'start_time': reservation.start_time.strftime('%Y-%m-%d %H:%M'),
            'price_per_hour': float(lot.price_per_hour),
            'redirect_url': url_for('user.user_dashboard')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Book Spot Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Booking failed: {str(e)}'}), 500

@user_bp.route('/vacate-reservation/<int:reservation_id>', methods=['POST'])
def vacate_reservation(reservation_id):
    """Vacate a parking spot (complete the reservation and calculate final cost)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    print(f"Vacate Reservation: User {user_id} vacating reservation {reservation_id}")
    
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != user_id:
        return jsonify({'success': False, 'message': 'Not your reservation'}), 403
    
    if reservation.status != ReservationStatus.ACTIVE:
        return jsonify({'success': False, 'message': 'Reservation is not active'}), 400
    
    try:
        spot = reservation.parking_spot
        lot = spot.parking_lot
        now = datetime.utcnow()
        
        # Calculate parking duration and cost
        duration_hours = (now - reservation.start_time).total_seconds() / 3600
        rounded_hours = int(duration_hours) + (1 if duration_hours % 1 > 0 else 0)
        reservation.total_cost = rounded_hours * float(lot.price_per_hour)
        
        # Update reservation as completed
        reservation.end_time = now
        reservation.status = ReservationStatus.COMPLETED
    
        # Free the parking spot
        spot.status = SpotStatus.AVAILABLE
    
        db.session.commit()
        
        # Update available spots count
        lot.update_available_spots()
        
        print(f"Vacate Reservation: Spot {spot.spot_number} vacated, final cost ₹{reservation.total_cost:.2f}")
        
        return jsonify({
            'success': True,
            'message': 'Spot vacated successfully',
            'total_cost': float(reservation.total_cost)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Vacate Reservation Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to vacate: {str(e)}'}), 500

@user_bp.route('/cancel-reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    """Cancel a parking reservation (user pays for time used)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    print(f"Cancel Reservation: User {user_id} cancelling reservation {reservation_id}")
    
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != user_id:
        return jsonify({'success': False, 'message': 'Not your reservation'}), 403
    
    if reservation.status != ReservationStatus.ACTIVE:
        return jsonify({'success': False, 'message': 'Reservation is not active'}), 400
    
    try:
        spot = reservation.parking_spot
        lot = spot.parking_lot
        now = datetime.utcnow()
        
        # Calculate cost for time used (minimum 1 hour charge)
        duration_hours = (now - reservation.start_time).total_seconds() / 3600
        charged_hours = max(1, int(duration_hours) + (1 if duration_hours % 1 > 0 else 0))
        reservation.total_cost = charged_hours * float(lot.price_per_hour)
        
        # Update reservation as cancelled
        reservation.end_time = now
        reservation.status = ReservationStatus.CANCELLED
        
        # Free the parking spot
        spot.status = SpotStatus.AVAILABLE
        
        db.session.commit()
        
        # Update available spots count
        lot.update_available_spots()
        
        print(f"Cancel Reservation: Reservation {reservation_id} cancelled, charged ₹{reservation.total_cost:.2f}")
        
        return jsonify({
            'success': True,
            'message': 'Reservation cancelled. You will be charged for time used.',
            'total_cost': float(reservation.total_cost)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Cancel Reservation Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to cancel: {str(e)}'}), 500
                           