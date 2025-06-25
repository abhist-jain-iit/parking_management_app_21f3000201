from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import ParkingLotStatus , SpotStatus , ReservationStatus
from datetime import datetime
from decimal import Decimal

class ParkingLot(BaseModel):
    __tablename__ = "parking_lots"
