# Base model class with essential fields only
from datetime import datetime
from app.extensions import db

class BaseModel(db.Model):
    # This won't create a table in the database
    __abstract__ = True
    
    # Primary key - every table needs this
    id = db.Column(db.Integer, primary_key=True)
    
    # When was this record created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Should also include:
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete flag - mark as deleted without actually removing from database
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Soft delete method - mark record as deleted
    def soft_delete(self, commit=True):
        self.is_deleted = True
        if commit:
            db.session.commit()
    
    # Restore deleted record
    def restore(self):
        self.is_deleted = False
        db.session.commit()

    # Get only active (not deleted) records
    @classmethod
    def get_active(cls):
        return cls.query.filter_by(is_deleted=False)

    # Convert model to dictionary for JSON responses
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.created_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"