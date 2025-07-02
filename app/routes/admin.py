from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from app.extensions import db
from datetime import datetime, timedelta
from app.models import *
import json
from app.decorators import require_permission
from sqlalchemy import func, or_
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

        # Jsonify for texting on postman
        # return jsonify({
        #     'stats': stats,
        #     'recent_reservations': [res.to_dict() for res in recent_reservations]
        # })

        return render_template('dashboards/admin_dashboard.html',
                               stats=stats,
                               recent_reservations=recent_reservations)

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
    # Display all users with search and filter options. 
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)

    query = User.query.filter(User.username != 'admin')

    if search:
        search_lower = search.lower()
        query = query.filter(or_(
            func.lower(User.username).contains(search_lower),
            func.lower(User.email).contains(search_lower),
            func.lower(User.first_name).contains(search_lower),
            func.lower(User.last_name).contains(search_lower)
        ))
        
    if role_filter:
        query = query.join(User.user_roles).join(UserRole.role).filter(
            func.lower(Role.name) == role_filter.lower()
        )
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    roles = Role.query.all()

    # Check if it's an API request (JSON expected)
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        users_list = [user.to_dict() for user in users.items]
        roles_list = [role.name for role in roles]
        
        return jsonify({
            "users": users_list,
            "roles": roles_list,
            "search": search,
            "role_filter": role_filter,
            "page": page,
            "total_pages": users.pages,
            "total_users": users.total
        })

    return render_template('admin/users/manage.html', 
                          users=users, 
                          roles=roles, 
                          search=search, 
                          role_filter=role_filter)


@admin_bp.route('/users/all')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def view_all_users():
    # View all registered users - comprehensive view with statistics.
    try:
        # Get all users except admin
        users = User.query.filter(User.username != 'admin').all()
        
        # Prepare user data with additional statistics
        users_data = []
        for user in users:
            total_reservations = user.reservations.count()
            active_reservations = user.reservations.filter_by(status='active').count()
            completed_reservations = user.reservations.filter_by(status='completed').count()
            cancelled_reservations = user.reservations.filter_by(status='cancelled').count()
            
            # Calculate total parking time (for completed reservations)
            total_hours = 0
            for reservation in user.reservations.filter_by(status='completed'):
                if reservation.start_time and reservation.end_time:
                    duration = reservation.end_time - reservation.start_time
                    total_hours += duration.total_seconds() / 3600
            
            # Get user roles
            user_roles = [role.name for role in user.roles] if hasattr(user, 'roles') else []
            
            users_data.append({
                'user': user,
                'roles': user_roles,
                'stats': {
                    'total_reservations': total_reservations,
                    'active_reservations': active_reservations,
                    'completed_reservations': completed_reservations,
                    'cancelled_reservations': cancelled_reservations,
                    'total_parking_hours': round(total_hours, 2),
                    'member_since': user.created_at,
                    'last_activity': user.updated_at
                }
            })
        
        # Sort by registration date (newest first)
        users_data.sort(key=lambda x: x['user'].created_at, reverse=True)
        
        # Summary statistics
        summary_stats = {
            'total_users': len(users_data),
            'active_users': len([u for u in users_data if u['stats']['active_reservations'] > 0]),
            'total_reservations': sum([u['stats']['total_reservations'] for u in users_data]),
            'total_parking_hours': round(sum([u['stats']['total_parking_hours'] for u in users_data]), 2)
        }
        
        # Get all available roles for potential filtering
        roles = Role.query.all()
        
        # Check if it's an API request (JSON expected)
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            # Prepare JSON response
            users_json = []
            for user_data in users_data:
                user_dict = user_data['user'].to_dict()
                user_dict['roles'] = user_data['roles']
                user_dict['stats'] = user_data['stats']
                users_json.append(user_dict)
            
            return jsonify({
                'success': True,
                'users': users_json,
                'summary_stats': summary_stats,
                'roles': [role.name for role in roles]
            })
        print({
                'success': True,
                'users': users_json,
                'summary_stats': summary_stats,
                'roles': [role.name for role in roles]
            })
        # Render HTML template
        return render_template('admin/users/all_users.html',
                             users_data=users_data,
                             summary_stats=summary_stats,
                             roles=roles)
                             
    except Exception as e:
        flash(f"Error loading users: {str(e)}", "error")
        
        # Handle error for both JSON and HTML requests
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': False,
                'error': str(e),
                'users': [],
                'summary_stats': {}
            }), 500
        
        return render_template('admin/users/all_users.html',
                             users_data=[],
                             summary_stats={},
                             roles=[])


@admin_bp.route('/users/<int:user_id>')
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def view_user_details(user_id):
    # View detailed information about a specific user.
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's reservation history with pagination
        page = request.args.get('page', 1, type=int)
        reservations_query = Reservation.query.filter_by(user_id=user_id).order_by(
            Reservation.created_at.desc()
        )
        reservations = reservations_query.paginate(page=page, per_page=10, error_out=False)
        
        # Get comprehensive user statistics
        total_reservations = Reservation.query.filter_by(user_id=user_id).count()
        active_reservations = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.ACTIVE
        ).count()
        completed_reservations = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.COMPLETED
        ).count()
        cancelled_reservations = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.CANCELLED
        ).count()
        
        # Calculate total spent and parking time
        total_spent = db.session.query(func.sum(Reservation.total_cost)).filter(
            Reservation.user_id == user_id,
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0
        
        # Calculate total parking hours for completed reservations
        total_hours = 0
        completed_res = Reservation.query.filter_by(
            user_id=user_id, 
            status=ReservationStatus.COMPLETED
        ).all()
        
        for reservation in completed_res:
            if reservation.start_time and reservation.end_time:
                duration = reservation.end_time - reservation.start_time
                total_hours += duration.total_seconds() / 3600
        
        # Get user roles
        user_roles = []
        if hasattr(user, 'user_roles'):
            user_roles = [ur.role.name for ur in user.user_roles]
        elif hasattr(user, 'roles'):
            user_roles = [role.name for role in user.roles]
        
        user_stats = {
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
            'completed_reservations': completed_reservations,
            'cancelled_reservations': cancelled_reservations,
            'total_spent': float(total_spent),
            'total_parking_hours': round(total_hours, 2),
            'account_created': user.created_at,
            'last_updated': user.updated_at,
            'user_roles': user_roles
        }
        
        # Check if it's an API request
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            user_dict = user.to_dict()
            user_dict['stats'] = user_stats
            user_dict['reservations'] = [res.to_dict() for res in reservations.items]
            
            return jsonify({
                'success': True,
                'user': user_dict,
                'reservations': {
                    'items': [res.to_dict() for res in reservations.items],
                    'page': page,
                    'pages': reservations.pages,
                    'total': reservations.total
                }
            })
        return render_template('admin/users/details.html', 
                             user=user, 
                             reservations=reservations, 
                             stats=user_stats)
                             
    except Exception as e:
        flash(f"Error loading user details: {str(e)}", "error")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
        return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def edit_user(user_id):
    """Edit user information - simplified version."""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            # Handle JSON requests
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Simple validation and update
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'phone' in data:
                user.phone = data['phone']
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.view_user_details', user_id=user_id))
            
        # GET request - show edit form (simplified)
        roles = Role.query.all()
        current_role_ids = []  # Simplified - no role fetching for now
        
        return render_template('admin/users/edit.html', 
                             user=user, 
                             roles=roles,
                             current_role_ids=current_role_ids)
                             
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete_simple', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
def delete_user_simple(user_id):
    # Simple delete user route for testing.
    if request.method == 'GET':
        # Show simple confirmation
        user = User.query.get_or_404(user_id)
        return f"""
        <h2>Delete User: {user.username}</h2>
        <p>Are you sure?</p>
        <form method="POST">
            <button type="submit">Yes, Delete</button>
            <a href="/admin/users">Cancel</a>
        </form>
        """
    
    # POST request - delete user
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        # Simple deletion without complex checks
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} deleted!', 'success')
        return redirect(url_for('admin.manage_users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.manage_users'))


# PARKING LOT ROUTES

@admin_bp.route('/parking')
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def manage_parking():
    # Main parking management dashboard with search and filter.
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    location_filter = request.args.get('location', '', type=str)
    
    query = ParkingLot.query
    
    if search:
        search_lower = search.lower()
        query = query.filter(or_(
            func.lower(ParkingLot.name).contains(search_lower),
            func.lower(ParkingLot.location).contains(search_lower),
            func.lower(ParkingLot.description).contains(search_lower)
        ))
    
    if location_filter:
        query = query.filter(func.lower(ParkingLot.location).contains(location_filter.lower()))
    
    parking_lots = query.paginate(page=page, per_page=10, error_out=False)
    
    # Get statistics for each parking lot
    lot_stats = []
    for lot in parking_lots.items:
        total_spots = lot.parking_spots.count()
        occupied = lot.parking_spots.filter_by(status='occupied').count()
        available = lot.parking_spots.filter_by(status='available').count()
        reserved = lot.parking_spots.filter_by(status='reserved').count()
        maintenance = lot.parking_spots.filter_by(status='maintenance').count()
        
        lot_stats.append({
            'lot': lot,
            'total_spots': total_spots,
            'occupied': occupied,
            'available': available,
            'reserved': reserved,
            'maintenance': maintenance,
            'occupancy_rate': round((occupied / total_spots * 100), 2) if total_spots > 0 else 0,
            'can_delete': occupied == 0 and reserved == 0
        })
    
    # Check if it's an API request
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'success': True,
            'parking_lots': [stat for stat in lot_stats],
            'search': search,
            'location_filter': location_filter,
            'page': page,
            'total_pages': parking_lots.pages,
            'total_lots': parking_lots.total
        })
    
    return render_template('admin/parking/manage.html', 
                          lot_stats=lot_stats, 
                          parking_lots=parking_lots,
                          search=search, 
                          location_filter=location_filter)

@admin_bp.route('/parking/lots/all')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_all_parking_lots():
    """View all parking lots - comprehensive view with statistics"""
    try:
        parking_lots = ParkingLot.query.all()
        
        lots_data = []
        for lot in parking_lots:
            total_spots = lot.parking_spots.count()
            occupied = lot.parking_spots.filter_by(status='occupied').count()
            available = lot.parking_spots.filter_by(status='available').count()
            reserved = lot.parking_spots.filter_by(status='reserved').count()
            maintenance = lot.parking_spots.filter_by(status='maintenance').count()
            
            # Calculate revenue from this lot
            lot_revenue = db.session.query(func.sum(Reservation.total_cost)).join(
                ParkingSpot, Reservation.parking_spot_id == ParkingSpot.id
            ).filter(
                ParkingSpot.parking_lot_id == lot.id,
                Reservation.status != ReservationStatus.CANCELLED
            ).scalar() or 0
            
            lots_data.append({
                'lot': lot,
                'stats': {
                    'total_spots': total_spots,
                    'occupied': occupied,
                    'available': available,
                    'reserved': reserved,
                    'maintenance': maintenance,
                    'occupancy_rate': round((occupied / total_spots * 100), 2) if total_spots > 0 else 0,
                    'revenue': float(lot_revenue),
                    'created_at': lot.created_at,
                    'updated_at': lot.updated_at
                }
            })
        
        # Summary statistics
        summary_stats = {
            'total_lots': len(lots_data),
            'total_spots': sum([l['stats']['total_spots'] for l in lots_data]),
            'total_occupied': sum([l['stats']['occupied'] for l in lots_data]),
            'total_available': sum([l['stats']['available'] for l in lots_data]),
            'total_revenue': round(sum([l['stats']['revenue'] for l in lots_data]), 2),
            'average_occupancy': round(sum([l['stats']['occupancy_rate'] for l in lots_data]) / len(lots_data), 2) if lots_data else 0
        }
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            lots_json = []
            for lot_data in lots_data:
                lot_dict = lot_data['lot'].to_dict() if hasattr(lot_data['lot'], 'to_dict') else {
                    'id': lot_data['lot'].id,
                    'name': lot_data['lot'].name,
                    'location': lot_data['lot'].location,
                    'description': lot_data['lot'].description,
                    'total_spots': lot_data['lot'].total_spots
                }
                lot_dict['stats'] = lot_data['stats']
                lots_json.append(lot_dict)
            
            return jsonify({
                'success': True,
                'parking_lots': lots_json,
                'summary_stats': summary_stats
            })
        
        return render_template('admin/parking/all_lots.html',
                             lots_data=lots_data,
                             summary_stats=summary_stats)
                             
    except Exception as e:
        flash(f"Error loading parking lots: {str(e)}", "error")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': False,
                'error': str(e),
                'parking_lots': [],
                'summary_stats': {}
            }), 500
        
        return render_template('admin/parking/all_lots.html',
                             lots_data=[],
                             summary_stats={})

@admin_bp.route('/parking/lots/create', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def create_parking_lot():
    """Create a new parking lot"""
    if request.method == 'POST':
        try:
            # Handle JSON requests
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            name = data.get('name')
            location = data.get('location')
            description = data.get('description')
            total_spots = int(data.get('total_spots', 0))
            
            # Create parking lot
            parking_lot = ParkingLot(
                name=name,
                location=location,
                description=description,
                total_spots=total_spots,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(parking_lot)
            db.session.flush()
            
            # Create parking spots
            for i in range(1, total_spots + 1):
                spot = ParkingSpot(
                    spot_number=f"{name}-{i:03d}",
                    parking_lot_id=parking_lot.id,
                    status='available',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(spot)
            
            db.session.commit()
            
            success_msg = f'Parking lot "{name}" created with {total_spots} spots!'
            
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'parking_lot': {
                        'id': parking_lot.id,
                        'name': parking_lot.name,
                        'location': parking_lot.location,
                        'total_spots': parking_lot.total_spots
                    }
                })
            
            flash(success_msg, 'success')
            return redirect(url_for('admin.manage_parking'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error creating parking lot: {str(e)}'
            
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 500
            
            flash(error_msg, 'error')
    
    return render_template('admin/parking/create_lot.html')

@admin_bp.route('/parking/lots/<int:lot_id>')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_parking_lot_details(lot_id):
    """View detailed information about a parking lot"""
    try:
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        # Get spots with pagination and filtering
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '', type=str)
        search = request.args.get('search', '', type=str)
        
        spots_query = parking_lot.parking_spots
        
        if status_filter:
            spots_query = spots_query.filter_by(status=status_filter)
        
        if search:
            spots_query = spots_query.filter(
                func.lower(ParkingSpot.spot_number).contains(search.lower())
            )
        
        spots = spots_query.paginate(page=page, per_page=50, error_out=False)
        
        # Get statistics
        stats = {
            'total': parking_lot.parking_spots.count(),
            'available': parking_lot.parking_spots.filter_by(status='available').count(),
            'occupied': parking_lot.parking_spots.filter_by(status='occupied').count(),
            'reserved': parking_lot.parking_spots.filter_by(status='reserved').count(),
            'maintenance': parking_lot.parking_spots.filter_by(status='maintenance').count()
        }
        
        # Calculate revenue
        lot_revenue = db.session.query(func.sum(Reservation.total_cost)).join(
            ParkingSpot, Reservation.parking_spot_id == ParkingSpot.id
        ).filter(
            ParkingSpot.parking_lot_id == lot_id,
            Reservation.status != ReservationStatus.CANCELLED
        ).scalar() or 0
        
        stats['revenue'] = float(lot_revenue)
        stats['occupancy_rate'] = round((stats['occupied'] / stats['total'] * 100), 2) if stats['total'] > 0 else 0
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            lot_dict = {
                'id': parking_lot.id,
                'name': parking_lot.name,
                'location': parking_lot.location,
                'description': parking_lot.description,
                'total_spots': parking_lot.total_spots
            }
            
            return jsonify({
                'success': True,
                'parking_lot': lot_dict,
                'stats': stats,
                'spots': {
                    'items': [{
                        'id': spot.id,
                        'spot_number': spot.spot_number,
                        'status': spot.status,
                        'created_at': spot.created_at.isoformat() if spot.created_at else None
                    } for spot in spots.items],
                    'page': page,
                    'pages': spots.pages,
                    'total': spots.total
                }
            })
        
        return render_template('admin/parking/lot_details.html', 
                             parking_lot=parking_lot, 
                             spots=spots, 
                             stats=stats, 
                             status_filter=status_filter,
                             search=search)
                             
    except Exception as e:
        flash(f"Error loading parking lot details: {str(e)}", "error")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.manage_parking'))

@admin_bp.route('/parking/lots/<int:lot_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def edit_parking_lot(lot_id):
    """Edit parking lot details"""
    try:
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        if request.method == 'POST':
            # Handle JSON requests
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            name = data.get('name')
            location = data.get('location')
            description = data.get('description')
            new_total_spots = int(data.get('total_spots', 0))
            
            # Get current number of spots
            current_spots = parking_lot.parking_spots.count()
            occupied_spots = parking_lot.parking_spots.filter_by(status='occupied').count()
            reserved_spots = parking_lot.parking_spots.filter_by(status='reserved').count()
            
            # Validate spot reduction
            if new_total_spots < current_spots:
                if occupied_spots > 0 or reserved_spots > 0:
                    error_msg = f'Cannot reduce spots. {occupied_spots} occupied and {reserved_spots} reserved spots exist.'
                    
                    if request.content_type == 'application/json':
                        return jsonify({'success': False, 'error': error_msg}), 400
                    
                    flash(error_msg, 'error')
                    return render_template('admin/parking/edit_lot.html', parking_lot=parking_lot)
                
                # Remove excess spots (only available ones)
                excess_spots = current_spots - new_total_spots
                spots_to_remove = parking_lot.parking_spots.filter_by(status='available').limit(excess_spots).all()
                
                for spot in spots_to_remove:
                    db.session.delete(spot)
            
            elif new_total_spots > current_spots:
                # Add new spots
                spots_to_add = new_total_spots - current_spots
                for i in range(current_spots + 1, new_total_spots + 1):
                    spot = ParkingSpot(
                        spot_number=f"{name}-{i:03d}",
                        parking_lot_id=parking_lot.id,
                        status='available',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(spot)
            
            # Update parking lot details
            parking_lot.name = name
            parking_lot.location = location
            parking_lot.description = description
            parking_lot.total_spots = new_total_spots
            parking_lot.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            success_msg = f'Parking lot "{name}" updated successfully!'
            
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'parking_lot': {
                        'id': parking_lot.id,
                        'name': parking_lot.name,
                        'location': parking_lot.location,
                        'total_spots': parking_lot.total_spots
                    }
                })
            
            flash(success_msg, 'success')
            return redirect(url_for('admin.manage_parking'))
            
        # GET request
        return render_template('admin/parking/edit_lot.html', parking_lot=parking_lot)
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error updating parking lot: {str(e)}'
        
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('admin.manage_parking'))

@admin_bp.route('/parking/lots/<int:lot_id>/delete', methods=['POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def delete_parking_lot(lot_id):
    """Delete parking lot - only if all spots are empty"""
    try:
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        # Check if any spots are occupied or reserved
        occupied_spots = parking_lot.parking_spots.filter_by(status='occupied').count()
        reserved_spots = parking_lot.parking_spots.filter_by(status='reserved').count()
        
        if occupied_spots > 0 or reserved_spots > 0:
            error_msg = f'Cannot delete parking lot "{parking_lot.name}". {occupied_spots} occupied and {reserved_spots} reserved spots exist.'
            
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 400
            
            flash(error_msg, 'error')
            return redirect(url_for('admin.manage_parking'))
        
        # Delete all parking spots first
        for spot in parking_lot.parking_spots:
            db.session.delete(spot)
        
        # Delete the parking lot
        lot_name = parking_lot.name
        db.session.delete(parking_lot)
        db.session.commit()
        
        success_msg = f'Parking lot "{lot_name}" deleted successfully!'
        
        if request.content_type == 'application/json':
            return jsonify({'success': True, 'message': success_msg})
        
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting parking lot: {str(e)}'
        
        if request.content_type == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
    
    return redirect(url_for('admin.manage_parking'))

@admin_bp.route('/parking/lots/search')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def search_parking_lots():
    """Advanced search for parking lots"""
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

@admin_bp.route('/parking/spots')
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def manage_parking_spots():
    """Manage all parking spots with search and filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    lot_filter = request.args.get('lot_id', '', type=str)
    
    query = ParkingSpot.query
    
    if search:
        query = query.filter(func.lower(ParkingSpot.spot_number).contains(search.lower()))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if lot_filter:
        query = query.filter_by(parking_lot_id=int(lot_filter))
    
    spots = query.paginate(page=page, per_page=50, error_out=False)
    
    # Get all parking lots for filter dropdown
    parking_lots = ParkingLot.query.all()
    
    # Get summary statistics
    stats = {
        'total': ParkingSpot.query.count(),
        'available': ParkingSpot.query.filter_by(status='available').count(),
        'occupied': ParkingSpot.query.filter_by(status='occupied').count(),
        'reserved': ParkingSpot.query.filter_by(status='reserved').count(),
        'maintenance': ParkingSpot.query.filter_by(status='maintenance').count()
    }
    
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        spots_json = []
        for spot in spots.items:
            spot_dict = {
                'id': spot.id,
                'spot_number': spot.spot_number,
                'status': spot.status,
                'parking_lot_id': spot.parking_lot_id,
                'parking_lot_name': spot.parking_lot.name if spot.parking_lot else None
            }
            spots_json.append(spot_dict)
        
        return jsonify({
            'success': True,
            'spots': spots_json,
            'stats': stats,
            'parking_lots': [{'id': lot.id, 'name': lot.name} for lot in parking_lots],
            'search': search,
            'status_filter': status_filter,
            'lot_filter': lot_filter,
            'page': page,
            'total_pages': spots.pages,
            'total_spots': spots.total
        })
    
    return render_template('admin/parking/manage_spots.html',
                          spots=spots,
                          stats=stats,
                          parking_lots=parking_lots,
                          search=search,
                          status_filter=status_filter,
                          lot_filter=lot_filter)

@admin_bp.route('/parking/spots/all')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_all_parking_spots():
    """View all parking spots - comprehensive view with statistics"""
    try:
        parking_spots = ParkingSpot.query.all()
        
        spots_data = []
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
            
            spots_data.append({
                'spot': spot,
                'stats': {
                    'revenue': float(spot_revenue),
                    'total_reservations': Reservation.query.filter_by(parking_spot_id=spot.id).count(),
                    'active_reservations': Reservation.query.filter_by(
                        parking_spot_id=spot.id,
                        status=ReservationStatus.ACTIVE
                    ).count(),
                    'current_reservation': {
                        'id': current_reservation.id,
                        'user_name': current_reservation.user.name if current_reservation and current_reservation.user else None,
                        'start_time': current_reservation.start_time.isoformat() if current_reservation else None,
                        'end_time': current_reservation.end_time.isoformat() if current_reservation else None
                    } if current_reservation else None,
                    'created_at': spot.created_at,
                    'updated_at': spot.updated_at
                }
            })
        
        # Summary statistics
        summary_stats = {
            'total_spots': len(spots_data),
            'available_spots': len([s for s in spots_data if s['spot'].status == 'available']),
            'occupied_spots': len([s for s in spots_data if s['spot'].status == 'occupied']),
            'reserved_spots': len([s for s in spots_data if s['spot'].status == 'reserved']),
            'maintenance_spots': len([s for s in spots_data if s['spot'].status == 'maintenance']),
            'total_revenue': round(sum([s['stats']['revenue'] for s in spots_data]), 2),
            'total_reservations': sum([s['stats']['total_reservations'] for s in spots_data])
        }
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            spots_json = []
            for spot_data in spots_data:
                spot_dict = {
                    'id': spot_data['spot'].id,
                    'spot_number': spot_data['spot'].spot_number,
                    'status': spot_data['spot'].status,
                    'parking_lot_id': spot_data['spot'].parking_lot_id,
                    'parking_lot_name': spot_data['spot'].parking_lot.name if spot_data['spot'].parking_lot else None
                }
                spot_dict['stats'] = spot_data['stats']
                spots_json.append(spot_dict)
            
            return jsonify({
                'success': True,
                'parking_spots': spots_json,
                'summary_stats': summary_stats
            })
        
        return render_template('admin/parking/all_spots.html',
                             spots_data=spots_data,
                             summary_stats=summary_stats)
                             
    except Exception as e:
        flash(f"Error loading parking spots: {str(e)}", "error")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': False,
                'error': str(e),
                'parking_spots': [],
                'summary_stats': {}
            }), 500
        
        return render_template('admin/parking/all_spots.html',
                             spots_data=[],
                             summary_stats={})

@admin_bp.route('/parking/spots/create', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def create_parking_spot():
    """Create a new parking spot"""
    if request.method == 'POST':
        try:
            # Handle JSON requests
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            spot_number = data.get('spot_number')
            parking_lot_id = int(data.get('parking_lot_id'))
            status = data.get('status', 'available')
            
            # Validate parking lot exists
            parking_lot = ParkingLot.query.get(parking_lot_id)
            if not parking_lot:
                error_msg = 'Invalid parking lot selected.'
                
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                flash(error_msg, 'error')
                return render_template('admin/parking/create_spot.html',
                                     parking_lots=ParkingLot.query.all())
            
            # Check if spot number already exists in this lot
            existing_spot = ParkingSpot.query.filter_by(
                spot_number=spot_number,
                parking_lot_id=parking_lot_id
            ).first()
            
            if existing_spot:
                error_msg = f'Spot number "{spot_number}" already exists in this parking lot.'
                
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                flash(error_msg, 'error')
                return render_template('admin/parking/create_spot.html',
                                     parking_lots=ParkingLot.query.all())
            
            # Create parking spot
            parking_spot = ParkingSpot(
                spot_number=spot_number,
                parking_lot_id=parking_lot_id,
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(parking_spot)
            
            # Update parking lot total spots
            parking_lot.total_spots = parking_lot.parking_spots.count() + 1
            parking_lot.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            success_msg = f'Parking spot "{spot_number}" created successfully!'
            
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'parking_spot': {
                        'id': parking_spot.id,
                        'spot_number': parking_spot.spot_number,
                        'status': parking_spot.status,
                        'parking_lot_name': parking_lot.name
                    }
                })
            
            flash(success_msg, 'success')
            return redirect(url_for('admin.manage_parking_spots'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error creating parking spot: {str(e)}'
            
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 500
            
            flash(error_msg, 'error')
    
    # GET request
    parking_lots = ParkingLot.query.all()
    return render_template('admin/parking/create_spot.html', parking_lots=parking_lots)

@admin_bp.route('/parking/spots/<int:spot_id>')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def view_parking_spot_details(spot_id):
    """View detailed information about a parking spot"""
    try:
        parking_spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Get reservation history with pagination
        page = request.args.get('page', 1, type=int)
        reservations = Reservation.query.filter_by(parking_spot_id=spot_id).order_by(
            Reservation.created_at.desc()
        ).paginate(page=page, per_page=20, error_out=False)
        
        # Get current active reservation
        current_reservation = Reservation.query.filter_by(
            parking_spot_id=spot_id,
            status=ReservationStatus.ACTIVE
        ).first()
        
        # Calculate statistics
        stats = {
            'total_reservations': Reservation.query.filter_by(parking_spot_id=spot_id).count(),
            'active_reservations': Reservation.query.filter_by(
                parking_spot_id=spot_id,
                status=ReservationStatus.ACTIVE
            ).count(),
            'completed_reservations': Reservation.query.filter_by(
                parking_spot_id=spot_id,
                status=ReservationStatus.COMPLETED
            ).count(),
            'cancelled_reservations': Reservation.query.filter_by(
                parking_spot_id=spot_id,
                status=ReservationStatus.CANCELLED
            ).count(),
            'total_revenue': float(db.session.query(func.sum(Reservation.total_cost)).filter_by(
                parking_spot_id=spot_id
            ).filter(
                Reservation.status != ReservationStatus.CANCELLED
            ).scalar() or 0)
        }
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            spot_dict = {
                'id': parking_spot.id,
                'spot_number': parking_spot.spot_number,
                'status': parking_spot.status,
                'parking_lot_id': parking_spot.parking_lot_id,
                'parking_lot_name': parking_spot.parking_lot.name if parking_spot.parking_lot else None,
                'created_at': parking_spot.created_at.isoformat() if parking_spot.created_at else None,
                'updated_at': parking_spot.updated_at.isoformat() if parking_spot.updated_at else None
            }
            
            reservations_json = []
            for reservation in reservations.items:
                res_dict = {
                    'id': reservation.id,
                    'user_name': reservation.user.name if reservation.user else None,
                    'start_time': reservation.start_time.isoformat() if reservation.start_time else None,
                    'end_time': reservation.end_time.isoformat() if reservation.end_time else None,
                    'status': reservation.status.value if hasattr(reservation.status, 'value') else str(reservation.status),
                    'total_cost': float(reservation.total_cost)
                }
                reservations_json.append(res_dict)
            
            return jsonify({
                'success': True,
                'parking_spot': spot_dict,
                'stats': stats,
                'current_reservation': {
                    'id': current_reservation.id,
                    'user_name': current_reservation.user.name if current_reservation.user else None,
                    'start_time': current_reservation.start_time.isoformat() if current_reservation else None,
                    'end_time': current_reservation.end_time.isoformat() if current_reservation else None
                } if current_reservation else None,
                'reservations': {
                    'items': reservations_json,
                    'page': page,
                    'pages': reservations.pages,
                    'total': reservations.total
                }
            })
        
        return render_template('admin/parking/spot_details.html',
                             parking_spot=parking_spot,
                             stats=stats,
                             current_reservation=current_reservation,
                             reservations=reservations)
                             
    except Exception as e:
        flash(f"Error loading parking spot details: {str(e)}", "error")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.manage_parking_spots'))

@admin_bp.route('/parking/spots/<int:spot_id>/edit', methods=['GET', 'POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def edit_parking_spot(spot_id):
    """Edit parking spot details"""
    try:
        parking_spot = ParkingSpot.query.get_or_404(spot_id)
        
        if request.method == 'POST':
            # Handle JSON requests
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            spot_number = data.get('spot_number')
            parking_lot_id = int(data.get('parking_lot_id'))
            status = data.get('status')
            
            # Validate parking lot exists
            parking_lot = ParkingLot.query.get(parking_lot_id)
            if not parking_lot:
                error_msg = 'Invalid parking lot selected.'
                
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                flash(error_msg, 'error')
                return render_template('admin/parking/edit_spot.html',
                                     parking_spot=parking_spot,
                                     parking_lots=ParkingLot.query.all())
            
            # Check if spot number already exists in this lot (excluding current spot)
            existing_spot = ParkingSpot.query.filter_by(
                spot_number=spot_number,
                parking_lot_id=parking_lot_id
            ).filter(ParkingSpot.id != spot_id).first()
            
            if existing_spot:
                error_msg = f'Spot number "{spot_number}" already exists in this parking lot.'
                
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                flash(error_msg, 'error')
                return render_template('admin/parking/edit_spot.html',
                                     parking_spot=parking_spot,
                                     parking_lots=ParkingLot.query.all())
            
            # Check if spot can be changed to maintenance/unavailable
            if status in ['maintenance'] and parking_spot.status in ['occupied', 'reserved']:
                error_msg = 'Cannot change status of occupied or reserved spots to maintenance.'
                
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                flash(error_msg, 'error')
                return render_template('admin/parking/edit_spot.html',
                                     parking_spot=parking_spot,
                                     parking_lots=ParkingLot.query.all())
            
            # Update parking spot
            old_lot_id = parking_spot.parking_lot_id
            parking_spot.spot_number = spot_number
            parking_spot.parking_lot_id = parking_lot_id
            parking_spot.status = status
            parking_spot.updated_at = datetime.utcnow()
            
            # Update total spots count for both lots if lot changed
            if old_lot_id != parking_lot_id:
                old_lot = ParkingLot.query.get(old_lot_id)
                if old_lot:
                    old_lot.total_spots = old_lot.parking_spots.count() - 1
                    old_lot.updated_at = datetime.utcnow()
                
                parking_lot.total_spots = parking_lot.parking_spots.count() + 1
                parking_lot.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            success_msg = f'Parking spot "{spot_number}" updated successfully!'
            
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'parking_spot': {
                        'id': parking_spot.id,
                        'spot_number': parking_spot.spot_number,
                        'status': parking_spot.status,
                        'parking_lot_name': parking_lot.name
                    }
                })
            
            flash(success_msg, 'success')
            return redirect(url_for('admin.manage_parking_spots'))
            
        # GET request
        parking_lots = ParkingLot.query.all()
        return render_template('admin/parking/edit_spot.html',
                             parking_spot=parking_spot,
                             parking_lots=parking_lots)
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error updating parking spot: {str(e)}'
        
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('admin.manage_parking_spots'))

@admin_bp.route('/parking/spots/<int:spot_id>/delete', methods=['POST'])
@require_permission(PermissionType.MANAGE_PARKING.value)
@refresh_db_session
def delete_parking_spot(spot_id):
    """Delete parking spot - only if not occupied or reserved"""
    try:
        parking_spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Check if spot is occupied or reserved
        if parking_spot.status in ['occupied', 'reserved']:
            error_msg = f'Cannot delete parking spot "{parking_spot.spot_number}". Spot is currently {parking_spot.status}.'
            
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 400
            
            flash(error_msg, 'error')
            return redirect(url_for('admin.manage_parking_spots'))
        
        # Check for active reservations
        active_reservations = Reservation.query.filter_by(
            parking_spot_id=spot_id,
            status=ReservationStatus.ACTIVE
        ).count()
        
        if active_reservations > 0:
            error_msg = f'Cannot delete parking spot "{parking_spot.spot_number}". It has active reservations.'
            
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 400
            
            flash(error_msg, 'error')
            return redirect(url_for('admin.manage_parking_spots'))
        
        # Update parking lot total spots
        parking_lot = parking_spot.parking_lot
        spot_number = parking_spot.spot_number
        
        # Delete the parking spot
        db.session.delete(parking_spot)
        
        # Update lot total spots
        if parking_lot:
            parking_lot.total_spots = parking_lot.parking_spots.count() - 1
            parking_lot.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        success_msg = f'Parking spot "{spot_number}" deleted successfully!'
        
        if request.content_type == 'application/json':
            return jsonify({'success': True, 'message': success_msg})
        
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting parking spot: {str(e)}'
        
        if request.content_type == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
    
    return redirect(url_for('admin.manage_parking_spots'))

@admin_bp.route('/parking/spots/search')
@require_permission(PermissionType.VIEW_PARKING_DETAILS.value)
@refresh_db_session
def search_parking_spots():
    """Advanced search for parking spots"""
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    lot_id = request.args.get('lot_id', 0, type=int)
    availability = request.args.get('availability', '', type=str)  # available, occupied, reserved, maintenance
    
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

    """Quick update parking spot status"""
    try:
        parking_spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Handle JSON requests
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        new_status = data.get('status')
        
        if new_status not in ['available', 'occupied', 'reserved', 'maintenance']:
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
        
        if request.content_type == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
    
    return redirect(url_for('admin.manage_parking_spots'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def reset_user_password(user_id):
    """Reset a user's password to a temporary password."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Generate a temporary password
        import secrets
        import string
        
        # Generate a random 8-character password
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for i in range(8))
        
        # Hash and set the new password
        user.set_password(temp_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Password reset successfully for {user.username}. Temporary password: {temp_password}', 'success')
        
        # Return JSON response if requested
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': True,
                'message': 'Password reset successfully',
                'temporary_password': temp_password
            })
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting password: {str(e)}', 'error')
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def deactivate_user(user_id):
    """Deactivate a user account."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Set user status to inactive
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'User {user.username} has been deactivated successfully.', 'success')
        
        # Return JSON response if requested
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': True,
                'message': f'User {user.username} deactivated successfully'
            })
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deactivating user: {str(e)}', 'error')
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@require_permission(PermissionType.MANAGE_USERS.value)
@refresh_db_session
def activate_user(user_id):
    """Activate a user account."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Set user status to active
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'User {user.username} has been activated successfully.', 'success')
        
        # Return JSON response if requested
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': True,
                'message': f'User {user.username} activated successfully'
            })
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error activating user: {str(e)}', 'error')
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.view_user_details', user_id=user_id))


