from app.extensions import db
from app.models import (
    User, Role, UserRole, RoleType, GenderEnum, UserStatus,
    Permission, RolePermission, PermissionType,
    Continent, Country, State, City, GeographyStatus,
    ParkingLot, ParkingSpot, Reservation, ParkingLotStatus, SpotStatus
)
from decimal import Decimal
from app.Data.data import GEOGRAPHY_DATA, parking_lots_data, permissions_data, USERS_DATA

def create_roles():
    """Create the basic user roles - Admin and Regular User"""
    # Create admin role (full system access)
    admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
    if not admin_role:
        admin_role = Role(
            role_type=RoleType.ADMIN,
            name=RoleType.ADMIN.value,
            description="System administrator with full access"
        )
        db.session.add(admin_role)

    # Create regular user role (limited access)
    user_role = Role.query.filter_by(name=RoleType.USER.value).first()
    if not user_role:
        user_role = Role(
            role_type=RoleType.USER,
            name=RoleType.USER.value,
            description="Regular user with basic permissions"
        )
        db.session.add(user_role)
    
    db.session.commit()
    return admin_role, user_role

def create_admin_user():
    """Create the default admin user account"""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        # Create admin user with default credentials
        admin_user = User(
            email="admin@parkingsystem.com",
            username='admin',
            first_name='System',
            last_name='Administrator',
            phone='+911234567890',
            gender=GenderEnum.OTHER,
            status=UserStatus.ACTIVE
        )
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)
        db.session.flush()

        # Give admin user the admin role
        admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
        if admin_role:
            user_role_assignment = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            db.session.add(user_role_assignment)

    db.session.commit()
    return admin_user

def create_permissions():
    """Create all the system permissions (what users can and cannot do)"""
    created_permissions = []
    for name, perm_type, description in permissions_data:
        existing_permission = Permission.query.filter_by(permission_type=perm_type).first()
        if not existing_permission:
            permission = Permission(
                name=name,
                permission_type=perm_type,
                description=description
            )
            db.session.add(permission)
            created_permissions.append(permission)
        else:
            created_permissions.append(existing_permission)
    
    db.session.commit()
    return created_permissions

def assign_permissions_to_roles():
    """Give different permissions to different user roles"""
    admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
    user_role = Role.query.filter_by(name=RoleType.USER.value).first()
    
    if not admin_role or not user_role:
        return
    
    # Give admin ALL permissions (full system access)
    all_permissions = Permission.query.all()
    for permission in all_permissions:
        existing_role_perm = RolePermission.query.filter_by(
            role_id=admin_role.id,
            permission_id=permission.id
        ).first()
        
        if not existing_role_perm:
            role_permission = RolePermission(
                role_id=admin_role.id,
                permission_id=permission.id
            )
            db.session.add(role_permission)
    
    # Give regular users only basic permissions (book spots, view lots, etc.)
    user_permission_types = [perm_type for _, perm_type, _ in permissions_data 
                           if perm_type.name.startswith(('MAKE_', 'VIEW_', 'CANCEL_', 'PARK_', 'RELEASE_'))]
    
    # Always give users permission to search for parking spots
    if PermissionType.SEARCH_PARKING_SPOTS not in user_permission_types:
        user_permission_types.append(PermissionType.SEARCH_PARKING_SPOTS)
        
    for perm_type in user_permission_types:
        permission = Permission.get_by_type(perm_type)
        if permission:
            existing_role_perm = RolePermission.query.filter_by(
                role_id=user_role.id,
                permission_id=permission.id
            ).first()
            if not existing_role_perm:
                role_permission = RolePermission(
                    role_id=user_role.id,
                    permission_id=permission.id
                )
                db.session.add(role_permission)
    
    db.session.commit()

def create_geography_data():
    """Create sample geography data (continents, countries, states, cities)"""
    for continent_data in GEOGRAPHY_DATA['continents']:
        existing_continent = Continent.query.filter_by(name=continent_data['name']).first()
        if not existing_continent:
            # Create continent
            continent = Continent(
                name=continent_data['name'],
                code=continent_data['code'],
                status=GeographyStatus.ACTIVE
            )
            db.session.add(continent)
            db.session.flush()
            
            # Add countries for this continent
            if continent_data['name'] in GEOGRAPHY_DATA['countries']:
                for country_data in GEOGRAPHY_DATA['countries'][continent_data['name']]:
                    country = Country(
                        name=country_data['name'],
                        code=country_data['code'],
                        continent_id=continent.id,
                        status=GeographyStatus.ACTIVE
                    )
                    db.session.add(country)
                    db.session.flush()
                    
                    # Add states for this country
                    if country_data['name'] in GEOGRAPHY_DATA['states']:
                        for state_data in GEOGRAPHY_DATA['states'][country_data['name']]:
                            state = State(
                                name=state_data['name'],
                                code=state_data['code'],
                                country_id=country.id,
                                status=GeographyStatus.ACTIVE
                            )
                            db.session.add(state)
                            db.session.flush()
                            
                            # Add cities for this state
                            if state_data['name'] in GEOGRAPHY_DATA['cities']:
                                for city_data in GEOGRAPHY_DATA['cities'][state_data['name']]:
                                    city = City(
                                        name=city_data['name'],
                                        code=city_data['code'],
                                        state_id=state.id,
                                        status=GeographyStatus.ACTIVE
                                    )
                                    db.session.add(city)
    
    db.session.commit()

def create_sample_parking_data():
    """Create sample parking lots and parking spots"""
    for lot_data in parking_lots_data:
        city = City.query.filter_by(name=lot_data['city_name']).first()
        if city:
            existing_lot = ParkingLot.query.filter_by(name=lot_data['name']).first()
            if not existing_lot:
                # Create parking lot
                parking_lot = ParkingLot(
                    name=lot_data['name'],
                    address=lot_data['address'],
                    city_id=city.id,
                    total_spots=lot_data['total_spots'],
                    available_spots=lot_data['total_spots'],
                    status=ParkingLotStatus.ACTIVE,
                    price_per_hour=lot_data['price_per_hour']
                )
                db.session.add(parking_lot)
                db.session.flush()
                
                # Create individual parking spots in this lot
                for i in range(1, lot_data['total_spots'] + 1):
                    parking_spot = ParkingSpot(
                        spot_number=f"A{i:03d}",
                        parking_lot_id=parking_lot.id,
                        status=SpotStatus.AVAILABLE
                    )
                    db.session.add(parking_spot)
    
    db.session.commit()

def create_sample_users():
    """Create sample user accounts for testing"""
    for user_data in USERS_DATA:
        # Check for existing user by username, email, or phone
        existing_user = User.query.filter(
            (User.username == user_data['username']) |
            (User.email == user_data['email']) |
            (User.phone == user_data['phone'])
        ).first()
        if not existing_user:
            # Create user account
            user = User(
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone'],
                gender=user_data['gender'],
                status=user_data['status']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.flush()
            # Give user the regular user role
            user_role = Role.query.filter_by(name=RoleType.USER.value).first()
            if user_role:
                user_role_assignment = UserRole(
                    user_id=user.id,
                    role_id=user_role.id
                )
                db.session.add(user_role_assignment)
    db.session.commit()

def init_database(app):
    """Initialize the database with all required data (run once when app starts)"""
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            
            # Create user roles (admin and regular user)
            admin_role, user_role = create_roles()
            
            # Create system permissions
            create_permissions()
            
            # Assign permissions to roles (what each role can do)
            assign_permissions_to_roles()
            
            # Create admin user account
            create_admin_user()
            
            # Create sample user accounts
            create_sample_users()
            
            # Create sample geography data
            create_geography_data()
            
            # Create sample parking lots and spots
            create_sample_parking_data()
            
        except Exception as e:
            db.session.rollback()
            raise

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    init_database(app)