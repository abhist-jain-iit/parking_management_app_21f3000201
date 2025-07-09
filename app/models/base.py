from datetime import datetime
from app.extensions import db

class BaseModel(db.Model):
    __abstract__ = True 
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    def soft_delete(self, commit=True):
        self.is_deleted = True
        if commit:
            db.session.commit()
    
    def restore(self):
        self.is_deleted = False
        db.session.commit()
    
    @classmethod
    def get_active(cls):
        return cls.query.filter_by(is_deleted=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"