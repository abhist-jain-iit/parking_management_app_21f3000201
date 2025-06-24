# Enums provide a clean, scalable way to manage status values.
from enum import Enum

class UserStatus(Enum):

    # User account status enumeration.
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"

    @classmethod
    def get_choices(cls):
        return [(status.value , status.value.title()) for status in cls]


class RoleType(Enum):

    # System roles enumeration.
    ADMIN = "admin"
    USER = "user"

    @classmethod
    def get_choices(cls):
        return [(role.value , role.value.replace('_', ' ').title())for role in cls]


class ParkingLotStatus(Enum):
    # Parking lot status enumeration.
    ACTIVE = "active"
    INACTIVE  = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"
    UNDER_CONSTRUCTION = "under_construction"
    DELETED = "deleted"
    BANNED = "banned"

    @classmethod
    def get_choices(cls):
        return [(status.value , status.value.replace('_' , ' ').title()) for status in cls]


class SpotStatus(Enum):
    # Individual parking spot status
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    OUT_OF_ORDER = "out_of_order"
    MAINTENANCE = "maintenance"
    DELETED = "deleted"

    @classmethod
    def get_choices(cls):
        return [(status.value , status.value.replace('_' , ' ').title()) for status in cls]

class ReservationStatus(Enum):
    # Reservation status enumeration.

    ACTIVE = "active"
    COMPLETED = "completed"
    NOT_COMPLETED = "not_completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NO_SHOW = "no_show"
    
    @classmethod
    def get_choices(cls):
        return [(status.value, status.value.replace('_', ' ').title()) for status in cls]