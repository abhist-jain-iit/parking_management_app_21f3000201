# Base model class with common fields and functionality

from datetime import datetime
from app import db

class BaseModel(db.Model):
    # __abstract__ = True means this won't create a table in the database.
    __abstract__ = True

    id = db.Column(db.Integer , primary_key = True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)  # nullable=True because not all rows are deleted

    # User tracking
    created_by = db.Column(db.Integer, nullable=True)  # Can link to User.id with a ForeignKey if needed
    updated_by = db.Column(db.Integer, nullable=True)
    deleted_by = db.Column(db.Integer, nullable=True)

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # SOFT Delete: Deletion from database without actually deleting from the database.
    def soft_delete(self, deleted_by_user_id=None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    # To restore the deleted item.
    def restore(self , updated_user_id = None):
        self.is_deleted = False
        self.updated_by = updated_user_id
        self.deleted_at = None
        self.deleted_by = None
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_active(cls):
        return cls.query.filter_by(is_deleted=False)

    # Convert model instance to dictionary. Useful for JSON responses and debugging.
    def to_dict(self):
        return {
            'id' : self.id,
            'created_at' : self.created_at.isoformat() if self.created_at else None,
            'updated_at' : self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at' : self.deleted_at.isoformat() if self.deleted_at else None,
            'created_by' : self.created_by,
            'updated_by' : self.updated_by,
            'deleted_by' : self.deleted_by,
            'is_deleted' : self.is_deleted,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"
    
