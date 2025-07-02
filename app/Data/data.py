from decimal import Decimal
from app.models.enums import PermissionType

# Geography Data
GEOGRAPHY_DATA = {
    'continents': [
        {'name': 'Asia', 'code': 'AS'}
    ],
    'countries': {
        'Asia': [
            {'name': 'India', 'code': 'IN'}
        ]
    },
    'states': {
        'India': [
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Delhi', 'code': 'DL'}
        ]
    },
    'cities': {
        'Karnataka': [
            {'name': 'Bangalore', 'pin_code': '560001'},
            {'name': 'Mysore', 'pin_code': '570001'}
        ],
        'Maharashtra': [
            {'name': 'Mumbai', 'pin_code': '400001'},
            {'name': 'Pune', 'pin_code': '411001'}
        ],
        'Delhi': [
            {'name': 'New Delhi', 'pin_code': '110001'}
        ]
    }
}

# Parking Lots Data
parking_lots_data = [
    {
        'name': 'Central Mall Parking',
        'address': 'MG Road, Central Business District',
        'city_name': 'Bangalore',
        'total_spots': 150,
        'price_per_hour': 20.00
    },
    {
        'name': 'Tech Park Parking',
        'address': 'Electronic City, Phase 1',
        'city_name': 'Bangalore',
        'total_spots': 100,
        'price_per_hour': 15.00
    },
    {
        'name': 'Airport Parking',
        'address': 'Kempegowda International Airport',
        'city_name': 'Bangalore',
        'total_spots': 100,
        'price_per_hour': 25.00
    }
]

# Permissions Data
permissions_data = [
    ("Full System Access", PermissionType.FULL_SYSTEM_ACCESS, "Complete access to all system features"),
    ("Manage Users", PermissionType.MANAGE_USERS, "Create, edit, delete users"),
    ("Manage Parking", PermissionType.MANAGE_PARKING, "Create, edit, delete parking lots and spots"),
    ("View Analytics", PermissionType.VIEW_ANALYTICS, "View system analytics and reports"),
    ("View Parking Details", PermissionType.VIEW_PARKING_DETAILS, "View detailed parking information"),
    ("Make Reservation", PermissionType.MAKE_RESERVATION, "Make parking reservations"),
    ("View Reservations", PermissionType.VIEW_RESERVATIONS, "View own reservations"),
    ("Cancel Reservation", PermissionType.CANCEL_RESERVATION, "Cancel own reservations"),
    ("Park Vehicle", PermissionType.PARK_VEHICLE, "Park vehicle in reserved spot"),
    ("Release Parking Spot", PermissionType.RELEASE_PARKING_SPOT, "Release parking spot"),
    ("View Personal Summary", PermissionType.VIEW_PERSONAL_SUMMARY, "View personal parking summary"),
    ("Search Parking Spots", PermissionType.SEARCH_PARKING_SPOTS, "Search for available parking spots"),
]