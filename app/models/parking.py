# Parking system models
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import ParkingLotStatus, SpotStatus, ReservationStatus
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Numeric


class ParkingLot(BaseModel):
    __tablename__ = "parking_lots"
    # Basic information
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    
    # Capacity and pricing
    total_spots = db.Column(db.Integer, nullable=False, default=0)
    available_spots = db.Column(db.Integer, nullable=False, default=0)
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('10.00'))
    
    # Status
    status = db.Column(db.Enum(ParkingLotStatus), default=ParkingLotStatus.ACTIVE, nullable=False)
    
    # Relationships
    city = db.relationship('City', back_populates='parking_lots')
    parking_spots = db.relationship('ParkingSpot', back_populates='parking_lot', cascade='all, delete-orphan')
     
    # Update available spots count
    def update_available_spots(self):
        try:
            available_count = ParkingSpot.query.filter_by(
                parking_lot_id=self.id,
                status=SpotStatus.AVAILABLE,
                is_deleted=False  # soft delete filter
            ).count()
            if available_count > self.total_spots:
                raise ValueError("Available spots cannot exceed total spots")
            self.available_spots = available_count
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'address': self.address,
            'city_name': self.city.name if self.city else None,
            'total_spots': self.total_spots,
            'available_spots': self.available_spots,
            'price_per_hour': float(self.price_per_hour),
            'status': self.status.value
        })
        return base_dict

    def __repr__(self):
        return f'<ParkingLot {self.name}>'

class ParkingSpot(BaseModel):
    __tablename__ = "parking_spots"
    
    # Basic information
    spot_number = db.Column(db.String(10), nullable=False)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.Enum(SpotStatus), default=SpotStatus.AVAILABLE.value, nullable=False)
    
    # Relationships
    parking_lot = db.relationship('ParkingLot', back_populates='parking_spots')
    reservations = db.relationship('Reservation', back_populates='parking_spot')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('spot_number', 'parking_lot_id'),)
    
    # Helper methods
    def is_available(self):
        return self.status == SpotStatus.AVAILABLE
    
    def reserve(self):
        if self.status != SpotStatus.AVAILABLE:
            raise ValueError("Cannot reserve a non-available spot.")
        try:
            self.status = SpotStatus.RESERVED
            db.session.commit()
            self.parking_lot.update_available_spots()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def occupy(self):
        self.status = SpotStatus.OCCUPIED
        db.session.commit()
    
    def free(self):
        self.status = SpotStatus.AVAILABLE
        db.session.commit()
    
    @staticmethod
    def count_available():
        return ParkingSpot.query.filter_by(status=SpotStatus.AVAILABLE).count()

    @staticmethod
    def count_reserved():
        return ParkingSpot.query.filter_by(status=SpotStatus.RESERVED).count()

    @staticmethod
    def count_occupied():
        return ParkingSpot.query.filter_by(status=SpotStatus.OCCUPIED).count()

    @staticmethod
    def count_available_by_lot(lot_id):
        return ParkingSpot.query.filter_by(parking_lot_id=lot_id, status=SpotStatus.AVAILABLE).count()

    @staticmethod
    def count_reserved_by_lot(lot_id):
        return ParkingSpot.query.filter_by(parking_lot_id=lot_id, status=SpotStatus.RESERVED).count()

    @staticmethod
    def count_occupied_by_lot(lot_id):
        return ParkingSpot.query.filter_by(parking_lot_id=lot_id, status=SpotStatus.OCCUPIED).count()



    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'spot_number': self.spot_number,
            'parking_lot_name': self.parking_lot.name if self.parking_lot else None,
            'status': self.status.value
        })
        return base_dict

    def __repr__(self):
        return f'<ParkingSpot {self.spot_number}>'

class Reservation(BaseModel):
    __tablename__ = "reservations"
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    
    # Time information
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Vehicle and cost
    vehicle_number = db.Column(db.String(20), nullable=False)
    total_cost = db.Column(Numeric(10, 2), nullable=False)    

    # Status
    status = db.Column(db.Enum(ReservationStatus), default=ReservationStatus.ACTIVE, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='reservations')
    parking_spot = db.relationship('ParkingSpot', back_populates='reservations')
    
    # Calculate total cost based on duration
    def calculate_cost(self, hourly_rate):
        if not self.end_time or not self.start_time:
            raise ValueError("Start time and end time must be set")
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        
        duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
        rounded_hours = math.ceil(duration_hours)
        self.total_cost = Decimal(str(rounded_hours)) * hourly_rate

    
    # Cancel the reservation
    def cancel(self):
        if self.status in [ReservationStatus.CANCELLED, ReservationStatus.COMPLETED]:
            raise ValueError("Reservation already cancelled or completed.")
        
        self.status = ReservationStatus.CANCELLED
        if self.parking_spot:
            self.parking_spot.free()  # assume this updates the spot and lot
        # Refund logic (e.g., self.issue_refund())
        db.session.commit()
    
    # Complete the reservation
    def complete(self):
        self.status = ReservationStatus.COMPLETED
        if self.parking_spot:
            self.parking_spot.free()
        db.session.commit()
    
    # Get reservation duration in hours
    def get_duration_hours(self):
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'user_name': self.user.username if self.user else None,
            'parking_lot_name': self.parking_spot.parking_lot.name if self.parking_spot else None,
            'spot_number': self.parking_spot.spot_number if self.parking_spot else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'vehicle_number': self.vehicle_number,
            'total_cost': float(self.total_cost),
            'status': self.status.value,
            'duration_hours': self.get_duration_hours()
        })
        return base_dict

    def __repr__(self):
        return f'<Reservation {self.vehicle_number}>'