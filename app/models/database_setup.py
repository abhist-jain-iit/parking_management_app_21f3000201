from app.extensions import db
from app.models import  User , Role,  RoleType, UserStatus , GenderEnum

def init_database(app):
    # Initialize database with tables and default data
    with app.app_context():

        print("🗄️ Creating database tables...")

        db.create_all()

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
            admin_user.set_password('1234567890')
            db.session.add(admin_user)
            db.session.flush()  # Get the ID without committing
            super_admin_role = Role.query.filter_by(name=RoleType.ADMIN.value).first()

            if super_admin_role:
                admin_user.add_role(super_admin_role)

                print("✅ Created admin user (username: admin, password: 1234567890)")
        else:
            print("⚠️  Admin user already exists")

        db.session.commit()
        
        print("🎉 Database initialization completed!")
        print("\n📊 Summary:")
        print(f"   Roles: {Role.query.count()}")
        print(f"   Users: {User.query.count()}")
        print("\n🔐 Default login:")
        print("   Username: admin")
        print("   Password: 1234567890")

if __name__ == '__main__':
    init_database()