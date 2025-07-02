from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime, timedelta
from app.models import *
from app.decorators import require_permission
from sqlalchemy import func, or_
from decimal import Decimal
import math

user_bp = Blueprint('user', __name__)

def require_user_login(f):
    """Decorator to require user login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/dashboard')
@require_user_login
def user_dashboard():
    """User dashboard with personal statistics and recent activity"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get user statistics
        total_reservations = Reservation.query.filter_by(user_id=user_id).count()
        active_reservations = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.ACTIVE
        ).count()
        completed_reservations = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.COMPLETED
        ).count()
        
        # Calculate total spent
        total_spent = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.user_id == user_id,
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0
        
        # Get recent reservations
        recent_reservations = Reservation.query.filter_by(
            user_id=user_id
        ).order_by(Reservation.created_at.desc()).limit(5).all()
        
        # Get available parking lots
        available_lots = ParkingLot.query.filter(
            ParkingLot.status == ParkingLotStatus.ACTIVE,
            ParkingLot.available_spots > 0
        ).all()
        
        stats = {
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
            'completed_reservations': completed_reservations,
            'total_spent': float(total_spent),
            'available_lots': len(available_lots)
        }
        
        return render_template('dashboards/user_dashboard.html',
                             user=user,
                             stats=stats,
                             recent_reservations=recent_reservations,
                             available_lots=available_lots)
                             
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboards/user_dashboard.html',
                             user=None,
                             stats={},
                             recent_reservations=[],
                             available_lots=[])

@user_bp.route('/parking-lots')
@require_user_login
def view_parking_lots():
    """View all available parking lots"""
    try:
        search = request.args.get('search', '', type=str)
        location_filter = request.args.get('location', '', type=str)
        price_filter = request.args.get('price_range', '', type=str)
        
        query = ParkingLot.query.filter(ParkingLot.status == ParkingLotStatus.ACTIVE)
        
        if search:
            search_lower = search.lower()
            query = query.filter(or_(
                func.lower(ParkingLot.name).contains(search_lower),
                func.lower(ParkingLot.address).contains(search_lower)
            ))
        
        if location_filter:
            query = query.join(ParkingLot.city).filter(
                func.lower(City.name).contains(location_filter.lower())
            )
        
        if price_filter:
            if price_filter == 'low':
                query = query.filter(ParkingLot.price_per_hour <= 20)
            elif price_filter == 'medium':
                query = query.filter(ParkingLot.price_per_hour.between(20, 30))
            elif price_filter == 'high':
                query = query.filter(ParkingLot.price_per_hour >= 30)
        
        parking_lots = query.all()
        
        return render_template('user/parking_lots.html',
                             parking_lots=parking_lots,
                             search=search,
                             location_filter=location_filter,
                             price_filter=price_filter)
                             
    except Exception as e:
        flash(f"Error loading parking lots: {str(e)}", "error")
        return render_template('user/parking_lots.html',
                             parking_lots=[],
                             search='',
                             location_filter='',
                             price_filter='')

@user_bp.route('/reserve/<int:lot_id>', methods=['GET', 'POST'])
@require_user_login
def reserve_parking(lot_id):
    """Reserve a parking spot in the selected lot"""
    try:
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        if parking_lot.available_spots <= 0:
            flash('No available spots in this parking lot.', 'error')
            return redirect(url_for('user.view_parking_lots'))
        
        if request.method == 'POST':
            vehicle_number = request.form.get('vehicle_number', '').upper()
            duration_hours = int(request.form.get('duration_hours', 1))
            
            if not vehicle_number:
                flash('Vehicle number is required.', 'error')
                return render_template('user/reserve_parking.html', parking_lot=parking_lot)
            
            if duration_hours < 1 or duration_hours > 24:
                flash('Duration must be between 1 and 24 hours.', 'error')
                return render_template('user/reserve_parking.html', parking_lot=parking_lot)
            
            # Find an available spot
            available_spot = ParkingSpot.query.filter_by(
                parking_lot_id=lot_id,
                status=SpotStatus.AVAILABLE
            ).first()
            
            if not available_spot:
                flash('No available spots at this time.', 'error')
                return redirect(url_for('user.view_parking_lots'))
            
            # Calculate cost
            total_cost = parking_lot.price_per_hour * duration_hours
            
            # Create reservation
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(hours=duration_hours)
            
            reservation = Reservation(
                user_id=session['user_id'],
                parking_spot_id=available_spot.id,
                vehicle_number=vehicle_number,
                start_time=start_time,
                end_time=end_time,
                total_cost=total_cost,
                status=ReservationStatus.ACTIVE
            )
            
            # Update spot status
            available_spot.status = SpotStatus.RESERVED
            
            # Update lot available spots
            parking_lot.available_spots -= 1
            
            db.session.add(reservation)
            db.session.commit()
            
            flash(f'Parking reserved successfully! Spot: {available_spot.spot_number}', 'success')
            return redirect(url_for('user.view_reservations'))
        
        return render_template('user/reserve_parking.html', parking_lot=parking_lot)
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error making reservation: {str(e)}", "error")
        return redirect(url_for('user.view_parking_lots'))

@user_bp.route('/reservations')
@require_user_login
def view_reservations():
    """View user's reservations"""
    try:
        user_id = session.get('user_id')
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '', type=str)
        
        query = Reservation.query.filter_by(user_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=ReservationStatus(status_filter))
        
        reservations = query.order_by(
            Reservation.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)
        
        return render_template('user/reservations.html',
                             reservations=reservations,
                             status_filter=status_filter)
                             
    except Exception as e:
        flash(f"Error loading reservations: {str(e)}", "error")
        return render_template('user/reservations.html',
                             reservations=None,
                             status_filter='')

@user_bp.route('/reservations/<int:reservation_id>/park', methods=['POST'])
@require_user_login
def park_vehicle(reservation_id):
    """Mark vehicle as parked (change status to occupied)"""
    try:
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=session['user_id']
        ).first_or_404()
        
        if reservation.status != ReservationStatus.ACTIVE:
            flash('Invalid reservation status.', 'error')
            return redirect(url_for('user.view_reservations'))
        
        # Update spot status to occupied
        parking_spot = reservation.parking_spot
        parking_spot.status = SpotStatus.OCCUPIED
        
        db.session.commit()
        
        flash('Vehicle parked successfully!', 'success')
        return redirect(url_for('user.view_reservations'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error parking vehicle: {str(e)}", "error")
        return redirect(url_for('user.view_reservations'))

@user_bp.route('/reservations/<int:reservation_id>/release', methods=['POST'])
@require_user_login
def release_parking(reservation_id):
    """Release parking spot (complete reservation)"""
    try:
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=session['user_id']
        ).first_or_404()
        
        if reservation.status != ReservationStatus.ACTIVE:
            flash('Invalid reservation status.', 'error')
            return redirect(url_for('user.view_reservations'))
        
        # Update reservation status to completed
        reservation.status = ReservationStatus.COMPLETED
        
        # Update spot status to available
        parking_spot = reservation.parking_spot
        parking_spot.status = SpotStatus.AVAILABLE
        
        # Update lot available spots
        parking_lot = parking_spot.parking_lot
        parking_lot.available_spots += 1
        
        db.session.commit()
        
        flash('Parking spot released successfully!', 'success')
        return redirect(url_for('user.view_reservations'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error releasing parking: {str(e)}", "error")
        return redirect(url_for('user.view_reservations'))

@user_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@require_user_login
def cancel_reservation(reservation_id):
    """Cancel an active reservation"""
    try:
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=session['user_id']
        ).first_or_404()
        
        if reservation.status != ReservationStatus.ACTIVE:
            flash('Can only cancel active reservations.', 'error')
            return redirect(url_for('user.view_reservations'))
        
        # Update reservation status to cancelled
        reservation.status = ReservationStatus.CANCELLED
        
        # Update spot status to available
        parking_spot = reservation.parking_spot
        if parking_spot.status == SpotStatus.RESERVED:
            parking_spot.status = SpotStatus.AVAILABLE
            
            # Update lot available spots
            parking_lot = parking_spot.parking_lot
            parking_lot.available_spots += 1
        
        db.session.commit()
        
        flash('Reservation cancelled successfully!', 'success')
        return redirect(url_for('user.view_reservations'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling reservation: {str(e)}", "error")
        return redirect(url_for('user.view_reservations'))

@user_bp.route('/profile')
@require_user_login
def user_profile():
    """View and edit user profile"""
    try:
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)
        
        return render_template('user/profile.html', user=user)
        
    except Exception as e:
        flash(f"Error loading profile: {str(e)}", "error")
        return redirect(url_for('user.user_dashboard'))

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@require_user_login
def edit_profile():
    """Edit user profile"""
    try:
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            user.first_name = request.form.get('first_name', user.first_name)
            user.last_name = request.form.get('last_name', user.last_name)
            user.phone = request.form.get('phone', user.phone)
            
            # Update password if provided
            new_password = request.form.get('new_password')
            if new_password:
                confirm_password = request.form.get('confirm_password')
                if new_password != confirm_password:
                    flash('Passwords do not match.', 'error')
                    return render_template('user/edit_profile.html', user=user)
                
                user.set_password(new_password)
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.user_profile'))
        
        return render_template('user/edit_profile.html', user=user)
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating profile: {str(e)}", "error")
        return redirect(url_for('user.user_profile'))