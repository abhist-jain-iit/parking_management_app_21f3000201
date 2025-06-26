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
        return [(role.value , role.value.replace('_', ' ').title()) for role in cls]

class GenderEnum(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

    @classmethod
    def get_choices(cls):
        return [(status.value , status.value.title()) for status in cls]

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


class PermissionType(Enum):
    # Permission enumeration

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_GEOGRAPHY = "manage_geography"
    MANAGE_PARKING_LOTS = "manage_parking_lots"
    MANAGE_PARKING_SPOTS = "manage_parking_spots"
    VIEW_ALL_RESERVATIONS = "view_all_reservations"
    VIEW_ANALYTICS = "view_analytics"
    SYSTEM_ADMIN = "system_admin"

    # User Permissions
    MAKE_RESERVATION = "make_reservation"
    VIEW_OWN_RESERVATIONS = "view_own_reservations"
    CANCEL_RESERVATION = "cancel_reservation"
    VIEW_AVAILABLE_LOTS = "view_available_lots"
    UPDATE_PROFILE = "update_profile"

    @classmethod
    def get_choices(cls):
        return [(status.value , status.value.replace('_' , ' ').title()) for status in cls]


class GeographyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

    @classmethod
    def get_choices(cls):
        return [(status.value, status.value.title()) for status in cls]
