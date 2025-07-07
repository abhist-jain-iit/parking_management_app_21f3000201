from decimal import Decimal
from app.models import PermissionType

# Sample users (excluding admin)
USERS_DATA = [
    {
        'username': 'john_doe',
        'email': 'john@example.com',
        'phone': '+919876543210',
        'first_name': 'John',
        'last_name': 'Doe',
        'gender': 'male',
        'status': 'active',
        'password': 'John@1234'
    },
    {
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'phone': '+919812345678',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'gender': 'female',
        'status': 'inactive',
        'password': 'Jane@1234'
    },
    {
        'username': 'alex_kumar',
        'email': 'alex@example.com',
        'phone': '+919800112233',
        'first_name': 'Alex',
        'last_name': 'Kumar',
        'gender': 'other',
        'status': 'pending',
        'password': 'Alex@1234'
    },
    {
        'username': 'banned_user',
        'email': 'banned@example.com',
        'phone': '+919811122233',
        'first_name': 'Banned',
        'last_name': 'User',
        'gender': 'male',
        'status': 'banned',
        'password': 'Banned@1234'
    }
]

# Expanded geography data
GEOGRAPHY_DATA = {
    'continents': [
        {'name': 'Asia', 'code': 'AS'},
        {'name': 'Europe', 'code': 'EU'}
    ],
    'countries': {
        'Asia': [
            {'name': 'India', 'code': 'IN'},
            {'name': 'China', 'code': 'CN'}
        ],
        'Europe': [
            {'name': 'Germany', 'code': 'DE'},
            {'name': 'France', 'code': 'FR'}
        ]
    },
    'states': {
        'India': [
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Tamil Nadu', 'code': 'TN'}
        ],
        'China': [
            {'name': 'Guangdong', 'code': 'GD'},
            {'name': 'Beijing', 'code': 'BJ'}
        ],
        'Germany': [
            {'name': 'Bavaria', 'code': 'BY'},
            {'name': 'Berlin', 'code': 'BE'}
        ],
        'France': [
            {'name': 'Île-de-France', 'code': 'IDF'},
            {'name': 'Provence', 'code': 'PACA'}
        ]
    },
    'cities': {
        'Karnataka': [
            {'name': 'Bengaluru', 'pin_code': '560001'},
            {'name': 'Mysuru', 'pin_code': '570001'}
        ],
        'Maharashtra': [
            {'name': 'Mumbai', 'pin_code': '400001'},
            {'name': 'Pune', 'pin_code': '411001'}
        ],
        'Guangdong': [
            {'name': 'Guangzhou', 'pin_code': '510000'},
            {'name': 'Shenzhen', 'pin_code': '518000'}
        ],
        'Bavaria': [
            {'name': 'Munich', 'pin_code': '80331'},
            {'name': 'Nuremberg', 'pin_code': '90402'}
        ],
        'Île-de-France': [
            {'name': 'Paris', 'pin_code': '75000'}
        ]
    }
}

# Expanded parking lots for different cities
parking_lots_data = [
    {
        'name': 'Central Mall Parking',
        'address': 'MG Road, Bengaluru, Karnataka',
        'city_name': 'Bengaluru',
        'total_spots': 50,
        'price_per_hour': Decimal('25.00')
    },
    {
        'name': 'Tech Park Parking',
        'address': 'Electronic City, Bengaluru, Karnataka',
        'city_name': 'Bengaluru',
        'total_spots': 100,
        'price_per_hour': Decimal('20.00')
    },
    {
        'name': 'Airport Parking',
        'address': 'Kempegowda International Airport, Bengaluru',
        'city_name': 'Bengaluru',
        'total_spots': 200,
        'price_per_hour': Decimal('50.00')
    },
    {
        'name': 'Phoenix Mall Parking',
        'address': 'Whitefield, Bengaluru, Karnataka',
        'city_name': 'Bengaluru',
        'total_spots': 80,
        'price_per_hour': Decimal('30.00')
    },
    {
        'name': 'Mumbai Central Parking',
        'address': 'Dadar, Mumbai, Maharashtra',
        'city_name': 'Mumbai',
        'total_spots': 120,
        'price_per_hour': Decimal('40.00')
    },
    {
        'name': 'Pune Station Parking',
        'address': 'Pune Railway Station, Pune, Maharashtra',
        'city_name': 'Pune',
        'total_spots': 60,
        'price_per_hour': Decimal('22.00')
    },
    {
        'name': 'Guangzhou Tower Parking',
        'address': 'Canton Tower, Guangzhou, Guangdong',
        'city_name': 'Guangzhou',
        'total_spots': 90,
        'price_per_hour': Decimal('35.00')
    },
    {
        'name': 'Munich Hauptbahnhof Parking',
        'address': 'Central Station, Munich, Bavaria',
        'city_name': 'Munich',
        'total_spots': 70,
        'price_per_hour': Decimal('45.00')
    },
    {
        'name': 'Paris Centre Parking',
        'address': 'Châtelet, Paris, Île-de-France',
        'city_name': 'Paris',
        'total_spots': 110,
        'price_per_hour': Decimal('55.00')
    }
]
    
permissions_data = [
        # Admin permissions
        ('Manage Users', PermissionType.MANAGE_USERS, 'Access and manage all registered users'),
        ('Manage Parking', PermissionType.MANAGE_PARKING, 'Create, edit, delete parking lots and manage parking spots'),
        ('View Analytics', PermissionType.VIEW_ANALYTICS, 'Access system analytics and summary charts'),
        ('View Parking Details', PermissionType.VIEW_PARKING_DETAILS, 'View parked vehicle details for occupied spots'),
        ('Search Parking Spots', PermissionType.SEARCH_PARKING_SPOTS, 'Search for specific parking spots and check occupancy'),
        ('Full System Access', PermissionType.FULL_SYSTEM_ACCESS, 'Root access to all system functionalities'),
        
        # User permissions
        ('Make Reservation', PermissionType.MAKE_RESERVATION, 'Book and reserve parking spots'),
        ('View Reservations', PermissionType.VIEW_RESERVATIONS, 'View personal reservation history and current bookings'),
        ('Cancel Reservation', PermissionType.CANCEL_RESERVATION, 'Cancel own reservations'),
        ('Park Vehicle', PermissionType.PARK_VEHICLE, 'Change spot status to occupied when parking'),
        ('Release Parking Spot', PermissionType.RELEASE_PARKING_SPOT, 'Vacate and release parking spot'),
        ('View Personal Summary', PermissionType.VIEW_PERSONAL_SUMMARY, 'View personal parking history and summary charts'),
]