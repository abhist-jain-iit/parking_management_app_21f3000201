from app import db
from app.models.base import BaseModel
from datetime import datetime
from app.models.enums import UserStatus , RoleType , GenderEnum
from werkzeug.security import generate_password_hash , check_password_hash

class Role(BaseModel):
    __tablename__ = "roles"

    role_type = db.Column(db.Enum(RoleType) , nullable = False , default = RoleType.USER)
    name = db.Column(db.String(100) , nullable = False)
    description = db.Column(db.Text , nullable = False)

    users = db.relationship('UserRole' , back_populates = 'role' , cascade='all, delete', passive_deletes=True)

    def to_dict(self):
        return {
            "role_type" : self.role_type.value if self.role_type else None,
            "name" : self.name,
            "description" : self.description
        }

    def __repr__(self):
        return f'<Role {self.name}>'

class User(BaseModel):
    # Role model for flexible permission system
    __tablename__ = "users"

    # Basic and important user information:
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)

    f_name = db.Column(db.String(50) , nullable = False)
    l_name = db.Column(db.String(50), nullable = False)
    phone_number = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=False, default=GenderEnum.OTHER)

    # Status management using enum
    status = db.Column(db.Enum(UserStatus), default=UserStatus.PENDING, nullable=False)

    # Additional tracking fields
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)

    roles = db.relationship('UserRole' , back_populates = 'user' , foreign_keys='UserRole.user_id', cascade='all, delete', passive_deletes=True)

    # Let's define some functions.
    # Set password
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    # Check Password
    def check_password(self,password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user_name": self.user_name,
            "email": self.email,
            "name": f"{self.f_name} {self.l_name}",
            "gender": self.gender.value if self.gender else None,
            "status": self.status.value,
            "roles": [ur.role.name for ur in self.roles]
        }


    def __repr__(self):
        return f'<User {self.f_name} {self.l_name}>'

class UserRole(BaseModel):
    __tablename__ = "userrole"
    user_id = db.Column(db.Integer , db.ForeignKey('users.id') , nullable = False)
    role_id = db.Column(db.Integer , db.ForeignKey('roles.id') , nullable = False)

    # Additional fields for tracking
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='roles')
    role = db.relationship('Role', back_populates='users')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)

    def __repr__(self):
        return f"<UserRole {self.user.user_name if self.user else 'Unknown'} - {self.role.name if self.role else 'Unknown'}>"