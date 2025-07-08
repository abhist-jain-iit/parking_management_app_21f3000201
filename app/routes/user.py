from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime, timedelta
from app.models import *
from app.decorators import require_permission
from sqlalchemy import func, or_
from decimal import Decimal
from functools import wraps
from app.models.enums import PermissionType, ParkingLotStatus, SpotStatus
from flask_login import current_user, login_required
from app.models.parking import ParkingSpot, Reservation
from app.models.geography import Country, State, City

user_bp = Blueprint('user', __name__, url_prefix='/user')

# User dashboard route
@user_bp.route('/dashboard')
@require_permission(PermissionType.VIEW_PERSONAL_SUMMARY.value)
def user_dashboard():
    flash_msg = request.args.get('flash')
    if flash_msg:
        flash(flash_msg, 'success')
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to view your dashboard.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    active_reservations = [r for r in reservations if r.status.value == 'active']
    completed_reservations = [r for r in reservations if r.status.value == 'completed']
    cancelled_reservations = [r for r in reservations if r.status.value == 'cancelled']
    lots = ParkingLot.query.all()
    spots = ParkingSpot.query.filter_by(status='available').all()
    return render_template('dashboards/user_dashboard.html',
                           user=user,
                           active_reservations=active_reservations,
                           completed_reservations=completed_reservations,
                           cancelled_reservations=cancelled_reservations,
                           lots=lots,
                           spots=spots)

@user_bp.route('/search_lots', methods=['POST'])
@require_permission(PermissionType.SEARCH_PARKING_SPOTS.value)
def search_lots():
    data = request.get_json() or request.form
    country_id = data.get('country')
    state_id = data.get('state')
    city_id = data.get('city')
    lot_name = data.get('lot_name', '').strip()
    page = int(data.get('page', 1))
    per_page = int(data.get('per_page', 10))

    query = ParkingLot.query.filter(ParkingLot.status == ParkingLotStatus.ACTIVE)

    if city_id:
        query = query.filter(ParkingLot.city_id == city_id)
    elif state_id:
        city_ids = [c.id for c in City.query.filter_by(state_id=state_id).all()]
        if city_ids:
            query = query.filter(ParkingLot.city_id.in_(city_ids))
    elif country_id:
        state_ids = [s.id for s in State.query.filter_by(country_id=country_id).all()]
        city_ids = [c.id for c in City.query.filter(City.state_id.in_(state_ids)).all()]
        if city_ids:
            query = query.filter(ParkingLot.city_id.in_(city_ids))

    if lot_name:
        query = query.filter(ParkingLot.name.ilike(f"%{lot_name}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    lots = pagination.items

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

# @user_bp.route('/book_spot', methods=['POST'])
# @require_permission(PermissionType.MAKE_RESERVATION.value)
# def book_spot():
#     user_id = session.get('user_id')
#     if not user_id:
#         return jsonify({'success': False, 'message': 'Not logged in'}), 401
#     lot_id = request.json.get('lot_id')
#     spot_id = request.json.get('spot_id')
#     vehicle_number = request.json.get('vehicle_number')
#     lot = ParkingLot.query.get(lot_id)
#     if not lot:
#         return jsonify({'success': False, 'message': 'Lot not found'}), 404
#     if lot.status in [ParkingLotStatus.UNDER_MAINTENANCE, ParkingLotStatus.BANNED, ParkingLotStatus.INACTIVE]:
#         return jsonify({'success': False, 'message': f'Cannot book a spot in a lot that is {lot.status.value}.'}), 400
#     spot = ParkingSpot.query.get(spot_id)
#     if not spot or spot.parking_lot_id != lot.id:
#         return jsonify({'success': False, 'message': 'Spot not found in this lot.'}), 404
#     if spot.status != SpotStatus.AVAILABLE:
#         return jsonify({'success': False, 'message': f'Spot is not available for booking (current status: {spot.status.value}).'}), 400
#     now = datetime.utcnow()
#     reservation = Reservation(
#         user_id=user_id,
#         parking_spot_id=spot.id,
#         start_time=now,
#         end_time=now,  # will be updated when released
#         vehicle_number=vehicle_number,
#         total_cost=0,
#         status='active'
#     )
#     spot.status = SpotStatus.RESERVED
#     db.session.add(reservation)
#     db.session.commit()
#     lot.update_available_spots()
#     return jsonify({'success': True, 'reservation_id': reservation.id, 'spot_number': spot.spot_number})

@user_bp.route('/update_reservation_status', methods=['POST'])
@require_permission(PermissionType.PARK_VEHICLE.value)
def update_reservation_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    reservation_id = request.json.get('reservation_id')
    new_status = request.json.get('status')  # 'occupied' or 'released'
    reservation = Reservation.query.get(reservation_id)
    if not reservation or reservation.user_id != user_id:
        return jsonify({'success': False, 'message': 'Reservation not found'}), 404
    spot = reservation.parking_spot
    lot = spot.parking_lot
    now = datetime.utcnow()
    if new_status == 'occupied':
        spot.status = 'occupied'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Spot marked as occupied'})
    elif new_status == 'released':
        # Check release permission
        from app.decorators import require_permission as require_perm
        @require_perm(PermissionType.RELEASE_PARKING_SPOT.value)
        def release():
            spot.status = 'available'
            reservation.end_time = now
            duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
            rounded_hours = int(duration_hours) + (1 if duration_hours % 1 > 0 else 0)
            reservation.total_cost = rounded_hours * float(lot.price_per_hour)
            reservation.status = 'completed'
            db.session.commit()
            lot.update_available_spots()
            return jsonify({'success': True, 'message': 'Spot released', 'bill': reservation.total_cost})
        return release()
    else:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

@user_bp.route('/user_reservations', methods=['GET'])
@require_permission(PermissionType.VIEW_RESERVATIONS.value)
def user_reservations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    data = []
    total_time = 0
    total_spent = 0
    for r in reservations:
        duration = 0
        if r.status.value == 'completed' and r.end_time and r.start_time:
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
    return jsonify({'reservations': data, 'summary': summary})

@user_bp.route('/user_reservations_paginated', methods=['GET'])
@require_permission(PermissionType.VIEW_RESERVATIONS.value)
def user_reservations_paginated():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    status = request.args.get('status')  # 'active', 'completed', 'cancelled', or None for all
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    query = Reservation.query.filter_by(user_id=user_id)
    if status:
        query = query.filter(Reservation.status == status)
    query = query.order_by(Reservation.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reservations = pagination.items
    data = []
    for r in reservations:
        duration = 0
        if r.status.value == 'completed' and r.end_time and r.start_time:
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
@require_permission(PermissionType.VIEW_PERSONAL_SUMMARY.value)
def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to edit your profile.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        # Optionally add validation here
        user.username = username
        user.email = email
        user.phone = phone
        user.first_name = first_name
        user.last_name = last_name
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.user_dashboard'))
    return render_template('user/edit_profile.html', user=user)

@user_bp.route('/get_continents', methods=['GET'])
def get_continents():
    continents = Continent.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in continents])

@user_bp.route('/get_countries', methods=['GET'])
def get_countries():
    continent_id = request.args.get('continent_id')
    query = Country.query
    if continent_id:
        query = query.filter_by(continent_id=continent_id)
    countries = query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in countries])

@user_bp.route('/get_states', methods=['GET'])
def get_states():
    country_id = request.args.get('country_id')
    query = State.query
    if country_id:
        query = query.filter_by(country_id=country_id)
    states = query.all()
    return jsonify([{'id': s.id, 'name': s.name} for s in states])

@user_bp.route('/get_cities', methods=['GET'])
def get_cities():
    state_id = request.args.get('state_id')
    query = City.query
    if state_id:
        query = query.filter_by(state_id=state_id)
    cities = query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in cities])

@user_bp.route('/get_lots', methods=['GET'])
def get_lots():
    city_id = request.args.get('city_id')
    query = ParkingLot.query.filter_by(status='active')
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
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot.id).all()
    spot_dicts = [s.to_dict() for s in spots]
    return render_template('user/lot_details.html', lot=lot, spots=spot_dicts)

@user_bp.route('/book-reservation')
@require_permission(PermissionType.MAKE_RESERVATION.value)
def book_reservation():
    countries = Country.query.all()
    return render_template('user/book_reservation.html', countries=countries)

@user_bp.route('/api/states')
def api_get_states():
    country_id = request.args.get('country_id', type=int)
    states = State.query.filter_by(country_id=country_id).all() if country_id else []
    return jsonify([{'id': s.id, 'name': s.name} for s in states])

@user_bp.route('/api/cities')
def api_get_cities():
    state_id = request.args.get('state_id', type=int)
    cities = City.query.filter_by(state_id=state_id).all() if state_id else []
    return jsonify([{'id': c.id, 'name': c.name} for c in cities])

@user_bp.route('/api/lots')
def api_get_lots():
    country_id = request.args.get('country_id', type=int)
    state_id = request.args.get('state_id', type=int)
    city_id = request.args.get('city_id', type=int)
    from app.models.geography import City, State
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
    return jsonify([{
        'id': l.id,
        'name': l.name,
        'address': l.address,
        'available_spots': l.available_spots,
        'price_per_hour': float(l.price_per_hour)
    } for l in lots])

@user_bp.route('/api/lot-spots/<int:lot_id>')
def api_lot_spots(lot_id):
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot_id).all()
    return jsonify([{'id': s.id, 'spot_number': s.spot_number, 'status': s.status.value} for s in spots])

@user_bp.route('/book-spot/<int:spot_id>', methods=['POST'])
@login_required
@require_permission(PermissionType.MAKE_RESERVATION.value)
def book_spot(spot_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You must be logged in to book a spot.'}), 401
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status.value != 'available':
        return jsonify({'success': False, 'message': 'Spot is not available.'}), 400
    data = request.get_json()
    vehicle_number = data.get('vehicle_number', '').strip()
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    start_time = datetime.now()
    reservation = Reservation(
        user_id=current_user.id,
        parking_spot_id=spot.id,
        start_time=start_time,
        end_time=None,
        vehicle_number=vehicle_number,
        total_cost=0,
        status='active'
    )
    spot.status = 'reserved'
    db.session.add(reservation)
    db.session.commit()
    lot = spot.parking_lot
    return jsonify({
        'success': True,
        'message': f'Reservation confirmed! Spot {spot.spot_number} in lot {lot.name} booked.',
        'spot_number': spot.spot_number,
        'lot_name': lot.name,
        'lot_id': lot.id
    })

@user_bp.route('/vacate-reservation/<int:reservation_id>', methods=['POST'])
@login_required
def vacate_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    if reservation.status.value != 'active':
        return jsonify({'success': False, 'message': 'Only active reservations can be vacated.'}), 400
    reservation.status = 'pending_vacate'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Vacate request submitted. Awaiting admin approval.'})

@user_bp.route('/cancel-reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    if reservation.status.value != 'active':
        return jsonify({'success': False, 'message': 'Only active reservations can be cancelled.'}), 400
    reservation.status = 'cancelled'
    reservation.end_time = datetime.now()
    # Calculate bill for time parked (if any)
    if reservation.start_time:
        duration = (reservation.end_time - reservation.start_time).total_seconds() / 3600
        rate = reservation.parking_spot.parking_lot.price_per_hour if reservation.parking_spot and reservation.parking_spot.parking_lot else 0
        reservation.total_cost = round(duration * rate, 2)
    else:
        reservation.total_cost = 0
    if reservation.parking_spot:
        reservation.parking_spot.free()
    db.session.commit()
    return jsonify({'success': True, 'message': f'Reservation cancelled. Bill: ₹{reservation.total_cost}'})
                           