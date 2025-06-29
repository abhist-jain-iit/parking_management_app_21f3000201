from decimal import Decimal
from app.models import PermissionType

# Geography data for initialization
GEOGRAPHY_DATA = {
    'continents': [
        {'name': 'Asia', 'code': 'AS'}
    ],
    'countries': {
        'Asia': [{'name': 'India', 'code': 'IN'}],
    },
    'states': {
        'India': [
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Tamil Nadu', 'code': 'TN'}
        ]
    },
    'cities': {
        'Karnataka': [
            {'name': 'Bengaluru', 'pin_code': '560001'},
            {'name': 'Mysuru', 'pin_code': '570001'}
        ]
    }
}
 # Sample parking lots for different cities
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