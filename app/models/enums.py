# Enums for managing status values and types
from enum import Enum

class RoleType(Enum):
    # System roles
    ADMIN = "admin"
    USER = "user"

class UserStatus(Enum):
    # User account status
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class GenderEnum(Enum):
    # Gender options
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class PermissionType(Enum):
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_PARKING = "manage_parking"
    VIEW_ANALYTICS = "view_analytics"
    VIEW_PARKING_DETAILS = "view_parking_details"
    SEARCH_PARKING_SPOTS = "search_parking_spots"
    FULL_SYSTEM_ACCESS = "full_system_access"
    
    # User permissions
    MAKE_RESERVATION = "make_reservation"
    VIEW_RESERVATIONS = "view_reservations"
    CANCEL_RESERVATION = "cancel_reservation"
    PARK_VEHICLE = "park_vehicle"
    RELEASE_PARKING_SPOT = "release_parking_spot"
    VIEW_PERSONAL_SUMMARY = "view_personal_summary"

class GeographyStatus(Enum):
    # Geography status
    ACTIVE = "active"
    INACTIVE = "inactive"

class ParkingLotStatus(Enum):
    # Parking lot status
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class SpotStatus(Enum):
    # Individual parking spot status
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"

class ReservationStatus(Enum):
    # Reservation status
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"