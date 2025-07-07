from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime, timedelta
from app.models import *
from app.decorators import require_permission
from sqlalchemy import func, or_
from decimal import Decimal
from functools import wraps

user_bp = Blueprint('user', __name__, url_prefix='/user')

# User dashboard route
@user_bp.route('/dashboard')
def user_dashboard():
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
                           