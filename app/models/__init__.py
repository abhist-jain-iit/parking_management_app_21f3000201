# Models package initialization - import all models and enums
from .base import BaseModel
from .enums import (
    UserStatus, RoleType, GenderEnum, ParkingLotStatus, 
    SpotStatus, ReservationStatus, PermissionType, 
    GeographyStatus
)
from .user import User, Role, UserRole
from .permissions import Permission, RolePermission
from .geography import Continent, Country, State, City
from .parking import ParkingLot, ParkingSpot, Reservation

# Make all models available when importing from models package
__all__ = [
    # Base model
    'BaseModel',
    
    # Enums
    'UserStatus', 'RoleType', 'GenderEnum', 'ParkingLotStatus', 
    'SpotStatus', 'ReservationStatus', 'PermissionType', 'GeographyStatus',
    
    # User models
    'User', 'Role', 'UserRole',
    
    # Permission models
    'Permission', 'RolePermission',
    
    # Geography models
    'Continent', 'Country', 'State', 'City',
    
    # Parking models
    'ParkingLot', 'ParkingSpot', 'Reservation'
]

