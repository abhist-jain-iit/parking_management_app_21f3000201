from app.extensions import db
from app.models import (
    User, Role, UserRole, RoleType, GenderEnum, UserStatus,
    Permission, RolePermission, PermissionType,
    Continent, Country, State, City, GeographyStatus,
    ParkingLot, ParkingSpot, Reservation, ParkingLotStatus, SpotStatus
)
from decimal import Decimal
from app.Data.data import GEOGRAPHY_DATA , parking_lots_data , permissions_data 


def create_roles():

    print("Creating default roles...")
    # Admin role
    admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
    if not admin_role:
        admin_role = Role(
            role_type=RoleType.ADMIN,
            name=RoleType.ADMIN.value,
            description="System administrator with full access"
        )
        db.session.add(admin_role)
        print("Created admin role")
    else:
        print("Admin role already exists")

    # User role
    user_role = Role.query.filter_by(name=RoleType.USER.value).first()
    if not user_role:
        user_role = Role(
            role_type=RoleType.USER,
            name=RoleType.USER.value,
            description="Regular user with basic permissions"
        )
        db.session.add(user_role)
        print("Created user role")
    else:
        print("User role already exists")
    
    db.session.commit()
    return admin_role, user_role

def create_admin_user():
    print("Creating default admin user...")
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
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
        db.session.flush()  # Get ID without committing

        # Assign admin role
        admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
        if admin_role:
            user_role_assignment = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            db.session.add(user_role_assignment)

        print("✓ Created admin user (username: admin, password: Admin@123)")
    else:
        print("✓ Admin user already exists")

    db.session.commit()
    return admin_user

def create_permissions():
    # Create system permissions
    print("Creating permissions...")
    
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
            print(f"✓ Created permission: {name}")
        else:
            created_permissions.append(existing_permission)
            print(f"✓ Permission already exists: {name}")
    
    db.session.commit()
    return created_permissions


def assign_permissions_to_roles():
    # Assign permissions to roles (not individual users).
    print("Assigning permissions to roles...")
    
    # Get all roles
    admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
    user_role = Role.query.filter_by(name=RoleType.USER.value).first()
    
    if not admin_role or not user_role:
        print("Error: Required roles not found!")
        return
    
    # Assign ALL permissions to Admin role
    print(f"Assigning permissions to Admin role...")
    all_permissions = Permission.query.all()
    admin_permissions_added = 0
    
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
            admin_permissions_added += 1
    
    print(f"✓ Added {admin_permissions_added} permissions to Admin role")
    
    # Assign BASIC permissions to User role
    print(f"Assigning permissions to User role...")
    user_permission_types = [
        PermissionType.MAKE_RESERVATION,
        PermissionType.VIEW_RESERVATIONS,
        PermissionType.CANCEL_RESERVATION,
        PermissionType.PARK_VEHICLE,
        PermissionType.RELEASE_PARKING_SPOT,
        PermissionType.VIEW_PERSONAL_SUMMARY,
        PermissionType.SEARCH_PARKING_SPOTS,
    ]
    
    user_permissions = Permission.query.filter(
        Permission.permission_type.in_(user_permission_types)
    ).all()
    
    user_permissions_added = 0
    for permission in user_permissions:
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
            user_permissions_added += 1
    
    print(f"✓ Added {user_permissions_added} permissions to User role")
    
    # Commit all changes
    db.session.commit()
    print("✓ Successfully assigned permissions to roles")


def create_geography_data():
    # Initialize geography data.
    print("Creating geography data...")
    
    for continent_data in GEOGRAPHY_DATA['continents']:
        existing_continent = Continent.query.filter_by(name=continent_data['name']).first()
        if not existing_continent:
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
                                        state_id=state.id,
                                        pin_code=city_data.get('pin_code'),
                                        status=GeographyStatus.ACTIVE
                                    )
                                    db.session.add(city)
            
            print(f"✓ Created continent: {continent_data['name']}")
        else:
            print(f"✓ Continent already exists: {continent_data['name']}")
    
    db.session.commit()

def create_sample_parking_data():
    # Create sample parking lots and spots.
    print("Creating sample parking data...")
    
   
    for lot_data in parking_lots_data:
        city = City.query.filter_by(name=lot_data['city_name']).first()
        if city:
            existing_lot = ParkingLot.query.filter_by(name=lot_data['name']).first()
            if not existing_lot:
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
                
                # Create parking spots
                for i in range(1, lot_data['total_spots'] + 1):
                    parking_spot = ParkingSpot(
                        spot_number=f"A{i:03d}",
                        parking_lot_id=parking_lot.id,
                        status=SpotStatus.AVAILABLE
                    )
                    db.session.add(parking_spot)
                
                print(f"✓ Created parking lot: {lot_data['name']} with {lot_data['total_spots']} spots")
            else:
                print(f"✓ Parking lot already exists: {lot_data['name']}")
    
    db.session.commit()

def init_database(app):
    """Updated initialization function"""
    with app.app_context():
        try:
            print("=" * 50)
            print("INITIALIZING PARKING MANAGEMENT DATABASE")
            print("=" * 50)
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Create roles
            admin_role, user_role = create_roles()
            
            # Create permissions
            create_permissions()
            
            # Assign permissions to roles (NOT individual users)
            assign_permissions_to_roles()
            
            # Create admin user (this should come after role permissions are set)
            admin_user = create_admin_user()
            
            # Create geography data
            create_geography_data()
            
            # Create sample parking data
            create_sample_parking_data()
            
            print("\n" + "=" * 50)
            print("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            
            # Print summary
            print(f"\nSUMMARY:")
            print(f"   Roles: {Role.query.count()}")
            print(f"   Users: {User.query.count()}")
            print(f"   Permissions: {Permission.query.count()}")
            print(f"   Role-Permission Assignments: {RolePermission.query.count()}")
            print(f"   User-Role Assignments: {UserRole.query.count()}")
            print(f"   Continents: {Continent.query.count()}")
            print(f"   Countries: {Country.query.count()}")
            print(f"   States: {State.query.count()}")
            print(f"   Cities: {City.query.count()}")
            print(f"   Parking Lots: {ParkingLot.query.count()}")
            print(f"   Parking Spots: {ParkingSpot.query.count()}")
            
            print(f"\nDEFAULT LOGIN CREDENTIALS:")
            print(f"   Username: admin")
            print(f"   Password: Admin@123")
            print(f"   Email: admin@parkingsystem.com")
            
        except Exception as e:
            print(f" Error during database initialization: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    init_database(app)