from app.extensions import db
from app.models import (User, Role, PermissionType, RolePermission,
                       Permission, 
                       Continent, Country, State, City)
from app.models.enums RoleType, GenderEnum, UserStatus
from app.utils.geography_data import GEOGRAPHY_DATA

def init_database(app):
    # Initialize database with tables and default data
    with app.app_context():

        print("🗄️ Creating database tables...")
        db.create_all()

        print("👤 Creating default roles...")
        admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
        if not admin_role:
            admin_role = Role(
                role_type = RoleType.ADMIN,
                name = RoleType.ADMIN.value,
                description = "This is by default admin role."
            )
            db.session.add(admin_role)
            print("✅ Created admin role")
        else:
            print("⚠️  Admin role already exists")

        print("👤 Default User Role creation ...")
        user_role = Role.query.filter_by(name=RoleType.USER.value).first()
        if not user_role:
            user_role = Role(
                role_type = RoleType.USER,
                name = RoleType.USER.value,
                description = "This is by default user."
            )
            db.session.add(user_role)
            print("✅ Created User Role!")
        else:
            print("⚠️ User Rolealready present")


        print("👤 Creating default admin user...")

        admin_user = User.query.filter_by(user_name = 'admin').first()

        if not admin_user:
            admin_user = User(
                email = "superadmin@gmail.com",
                user_name = 'admin',
                f_name = 'super',
                l_name = 'admin',
                phone_number = '1234567890',
                gender = GenderEnum.OTHER,
                status = UserStatus.ACTIVE
            )
            admin_user.set_password('Admin@123')
            db.session.add(admin_user)
            db.session.flush()  # Get the ID without committing

            # Add admin role to user
            from app.models.user import UserRole
            admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()
            if admin_role:
                user_role_assignment = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    assigned_by=admin_user.id  # Self-assigned for initial admin
                )
                db.session.add(user_role_assignment)

            print("✅ Created admin user (username: admin, password: Admin@123)")
        else:
            print("⚠️  Admin user already exists")

        db.session.commit()
        
        print("🎉 Database initialization completed!")
        print("\n📊 Summary:")
        print(f"   Roles: {Role.query.count()}")
        print(f"   Users: {User.query.count()}")
        print("\n🔐 Default login:")
        print("   Username: admin")
        print("   Password: Admin@123")

if __name__ == '__main__':
    init_database()