from flask import Blueprint, render_template , redirect , request , url_for, flash, session , jsonify
from app.extensions import db
from datetime import datetime , timedelta
from app.models import *
import json
from app.decorators import require_permission # for permission
from sqlalchemy import func
from decimal import Decimal
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def refresh_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db.session.expire_all()  # clears SQLAlchemy cache
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard')
# @require_permission(PermissionType.FULL_SYSTEM_ACCESS.value)
@refresh_db_session
def admin_dashboard():

    # Main admin dashboard with overview statistics.
    try:
        #  Use this dummy reservation to test that everything is working fine.
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
        # Jsonify for texting on postman
        return jsonify({
            'stats': stats,
            'recent_reservations': [res.to_dict() for res in recent_reservations]
        })
        return render_template('admin_dashboard.html',
                               stats=stats,
                               recent_reservations=recent_reservations)

    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('admin_dashboard.html',
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