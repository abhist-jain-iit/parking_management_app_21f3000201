# User and Role models
from app.extensions import db 
import re
from app.models.base import BaseModel
from app.models.enums import UserStatus, RoleType, GenderEnum
from werkzeug.security import generate_password_hash, check_password_hash

class Role(BaseModel):
    __tablename__ = "roles"

    # Role type from enum
    role_type = db.Column(db.Enum(RoleType), nullable=False, default=RoleType.USER)
    # Role name
    name = db.Column(db.String(100), nullable=False, unique=True)
    # Role description
    description = db.Column(db.Text, nullable=True)
    # Relationship to users through UserRole
    user_roles = db.relationship('UserRole', back_populates='role', cascade='all, delete-orphan')
    # Relationship to permissions through RolePermission
    role_permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "role_type": self.role_type.value if self.role_type else None,
            "name": self.name,
            "description": self.description
        })
        return base_dict

    def __repr__(self):
        return f'<Role {self.name}>'

class User(BaseModel):
    __tablename__ = "users"

    # Basic user information
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)

    # Personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    # Gender and status
    gender = db.Column(db.Enum(GenderEnum), nullable=False, default=GenderEnum.OTHER)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.PENDING, nullable=False)

    # Relationships
    user_roles = db.relationship('UserRole', back_populates='user', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', back_populates='user')

    # Email validation
    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    # Password validation
    def validate_password(self, password):
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        return True, "Password is valid"

    # Set password with validation
    def set_password(self, password):
        is_valid, message = self.validate_password(password)
        if not is_valid:
            raise ValueError(message)
        self.password_hash = generate_password_hash(password)

    def validate_phone(self, key, number):
        if not re.match(r"^\+?[0-9]{10,15}$", number):
            raise ValueError("Invalid phone number format")
        return number

    # Check password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Get user's full name
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "phone": self.phone,
            "gender": self.gender.value if self.gender else None,
            "status": self.status.value,
            "roles": [ur.role.name for ur in self.user_roles]
        })
        return base_dict

    def __repr__(self):
        return f'<User {self.username}>'

class UserRole(BaseModel):
    __tablename__ = "user_roles"

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='user_roles')
    role = db.relationship('Role', back_populates='user_roles')

    # Prevent duplicate user-role assignments
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "user_name": self.user.username if self.user else None,
            "role_name": self.role.name if self.role else None
        })
        return base_dict

    def __repr__(self):
        return f"<UserRole {self.user.username if self.user else 'Unknown'} - {self.role.name if self.role else 'Unknown'}>"