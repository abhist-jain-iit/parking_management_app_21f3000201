# Permission models for role-based access control
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import PermissionType

class Permission(BaseModel):
    __tablename__ = "permissions"

    # Permission name and type
    name = db.Column(db.String(100), nullable=False, unique=True)
    permission_type = db.Column(db.Enum(PermissionType), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    # Relationship to roles through RolePermission
    role_permissions = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "permission_type": self.permission_type.value if self.permission_type else None,
            "description": self.description
        })
        return base_dict

    def __repr__(self):
        return f"<Permission {self.name}>"

class RolePermission(BaseModel):
    __tablename__ = "role_permissions"
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    
    # Relationships
    role = db.relationship('Role', back_populates='role_permissions')
    permission = db.relationship('Permission', back_populates='role_permissions')
    
    # Prevent duplicate role-permission assignments
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "role_name": self.role.name if self.role else None,
            "permission_name": self.permission.name if self.permission else None
        })
        return base_dict
    
    def __repr__(self):
        return f"<RolePermission {self.role.name if self.role else 'Unknown'} - {self.permission.name if self.permission else 'Unknown'}>"