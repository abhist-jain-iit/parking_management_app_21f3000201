from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import PermissionType

class Permission(BaseModel):
    __tablename__ = "permissions"
    name = db.Column(db.String(100) , nullable = False)
    permission_type = db.Column(db.Enum(PermissionType) , nullable = False)
    description = db.Column(db.Text , nullable = False)

    # Many-to-many relationship with roles
    roles = db.relationship('RolePermission', back_populates='permission', cascade='all, delete', passive_deletes=True)

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
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    role = db.relationship('Role', backref=db.backref('role_permissions', cascade='all, delete'))
    permission = db.relationship('Permission', back_populates='roles')
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)
    
    def __repr__(self):
        return f"<RolePermission {self.role.name if self.role else 'Unknown'} - {self.permission.name if self.permission else 'Unknown'}>"