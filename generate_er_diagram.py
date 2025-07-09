import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_er_diagram():
    # Set up the figure with better proportions
    fig, ax = plt.subplots(figsize=(26, 18))
    ax.set_xlim(0, 32)
    ax.set_ylim(0, 22)
    ax.axis('off')
    
    # Modern color scheme
    colors = {
        'primary': '#2563EB',      # Blue
        'secondary': '#7C3AED',    # Purple
        'success': '#059669',      # Green
        'warning': '#D97706',      # Orange
        'danger': '#DC2626',       # Red
        'light': '#F8FAFC',        # Light gray
        'dark': '#1E293B',         # Dark gray
        'border': '#E2E8F0',       # Border gray
        'text': '#334155',         # Text gray
        'accent': '#3B82F6',       # Accent blue
        'relationship': '#FEF3C7'   # Relationship table color
    }
    
    # Entity definitions with better positioning and larger sizes
    entities = {
        'User': {'pos': (2, 19), 'w': 5, 'h': 3, 'color': colors['primary']},
        'Role': {'pos': (10, 19), 'w': 4.5, 'h': 3, 'color': colors['secondary']},
        'Permission': {'pos': (18, 19), 'w': 5, 'h': 3, 'color': colors['success']},
        'UserRole': {'pos': (6, 15), 'w': 4, 'h': 2.5, 'color': colors['relationship']},
        'RolePermission': {'pos': (14, 15), 'w': 4, 'h': 2.5, 'color': colors['relationship']},
        'Continent': {'pos': (2, 11), 'w': 5, 'h': 3, 'color': colors['warning']},
        'Country': {'pos': (10, 11), 'w': 4.5, 'h': 3, 'color': colors['danger']},
        'State': {'pos': (18, 11), 'w': 4.5, 'h': 3, 'color': colors['primary']},
        'City': {'pos': (26, 11), 'w': 4.5, 'h': 3, 'color': colors['secondary']},
        'ParkingLot': {'pos': (2, 7), 'w': 5, 'h': 3, 'color': colors['success']},
        'ParkingSpot': {'pos': (10, 7), 'w': 4.5, 'h': 3, 'color': colors['warning']},
        'Reservation': {'pos': (18, 7), 'w': 5, 'h': 3, 'color': colors['danger']}
    }
    
    # Draw entities with modern styling
    for name, props in entities.items():
        x, y, w, h = props['pos'][0], props['pos'][1], props['w'], props['h']
        color = props['color']
        
        # Main entity box
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            facecolor=colors['light'],
            edgecolor=color,
            linewidth=3
        )
        ax.add_patch(box)
        
        # Entity name - LARGER AND BOLDER
        ax.text(x + w/2, y + h - 0.5, name, 
                ha='center', va='center', fontsize=18, fontweight='bold', color=color)
        
        # Attributes based on entity - LARGER FONT
        attrs = get_attributes(name)
        for i, attr in enumerate(attrs):
            ax.text(x + 0.3, y + h - 1 - i*0.4, f"• {attr}", 
                    ha='left', va='center', fontsize=12, fontweight='bold', color=colors['text'])
    
    # Draw ALL relationships correctly
    relationships = [
        # Many-to-Many: User ↔ Role (through UserRole)
        ((7, 20.5), (8, 16.5), 'N', colors['primary']),      # User to UserRole
        ((12.5, 20.5), (10, 16.5), 'N', colors['secondary']), # Role to UserRole
        
        # Many-to-Many: Role ↔ Permission (through RolePermission)
        ((14.5, 20.5), (14, 16.5), 'N', colors['secondary']), # Role to RolePermission
        ((20.5, 20.5), (18, 16.5), 'N', colors['success']),   # Permission to RolePermission
        
        # One-to-Many: User → Reservation
        ((7, 18.5), (18, 9.5), '1', colors['primary']),
        ((20.5, 9.5), (18, 9.5), 'N', colors['danger']),
        
        # One-to-Many: ParkingSpot → Reservation
        ((12.5, 9.5), (18, 9.5), '1', colors['warning']),
        ((20.5, 9.5), (18, 9.5), 'N', colors['danger']),
        
        # One-to-Many: ParkingLot → ParkingSpot
        ((7, 9.5), (10, 9.5), '1', colors['success']),
        ((12.5, 9.5), (10, 9.5), 'N', colors['warning']),
        
        # One-to-Many: City → ParkingLot
        ((28.5, 12.5), (7, 9.5), '1', colors['secondary']),
        ((7, 9.5), (7, 9.5), 'N', colors['success']),
        
        # One-to-Many: State → City
        ((22.5, 12.5), (28.5, 12.5), '1', colors['primary']),
        ((28.5, 12.5), (28.5, 12.5), 'N', colors['secondary']),
        
        # One-to-Many: Country → State
        ((14.5, 12.5), (22.5, 12.5), '1', colors['danger']),
        ((22.5, 12.5), (22.5, 12.5), 'N', colors['primary']),
        
        # One-to-Many: Continent → Country
        ((7, 12.5), (14.5, 12.5), '1', colors['warning']),
        ((14.5, 12.5), (14.5, 12.5), 'N', colors['danger'])
    ]
    
    for start, end, label, color in relationships:
        # Draw arrow
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='-|>', color=color, lw=3, shrinkA=20, shrinkB=20))
        
        # Label - LARGER AND BOLDER
        mid_x, mid_y = (start[0] + end[0])/2, (start[1] + end[1])/2
        ax.text(mid_x, mid_y, label, fontsize=14, fontweight='bold', 
                color=color, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.4", facecolor='white', edgecolor=color, alpha=0.9))
    
    # Title - LARGER
    ax.text(16, 21.5, 'Parking Management System', 
            ha='center', va='center', fontsize=28, fontweight='bold', color=colors['dark'])
    ax.text(16, 21, 'Entity Relationship Diagram (ERD)', 
            ha='center', va='center', fontsize=20, color=colors['text'])
    
    # Legend - LARGER
    legend_x, legend_y = 1, 3
    ax.text(legend_x, legend_y + 2.5, 'Legend', fontsize=18, fontweight='bold', color=colors['dark'])
    
    # Legend items - LARGER
    legend_items = [
        ('Entity', colors['primary']),
        ('Relationship Table', colors['relationship']),
        ('1 = One', colors['text']),
        ('N = Many', colors['text']),
        ('1:N = One-to-Many', colors['text']),
        ('N:M = Many-to-Many', colors['text'])
    ]
    
    for i, (text, color) in enumerate(legend_items):
        y_pos = legend_y + 2 - i*0.5
        if i < 2:  # Draw boxes for first two items
            ax.add_patch(FancyBboxPatch((legend_x, y_pos-0.3), 2, 0.6, 
                                       boxstyle="round,pad=0.1", facecolor=colors['light'], 
                                       edgecolor=color, linewidth=2))
        ax.text(legend_x + 2.2, y_pos, text, va='center', fontsize=14, fontweight='bold', color=color)
    
    # Additional info - LARGER
    ax.text(16, 2, 'PK = Primary Key | FK = Foreign Key', 
            ha='center', va='center', fontsize=16, color=colors['text'], style='italic')
    
    # Relationship explanations
    explanations = [
        ('User ↔ Role (N:M)', 'Users can have multiple roles, roles can have multiple users'),
        ('Role ↔ Permission (N:M)', 'Roles can have multiple permissions, permissions can be assigned to multiple roles'),
        ('User → Reservation (1:N)', 'One user can have many reservations'),
        ('ParkingSpot → Reservation (1:N)', 'One spot can have many reservations over time'),
        ('ParkingLot → ParkingSpot (1:N)', 'One lot has many parking spots'),
        ('City → ParkingLot (1:N)', 'One city can have many parking lots'),
        ('Geography Hierarchy (1:N)', 'Continent → Country → State → City')
    ]
    
    for i, (title, desc) in enumerate(explanations):
        y_pos = 1.5 - i*0.3
        ax.text(1, y_pos, f"• {title}: {desc}", fontsize=11, color=colors['text'])
    
    plt.tight_layout()
    plt.savefig('parking_management_er_diagram.pdf', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

def get_attributes(entity_name):
    """Return attributes for each entity"""
    attributes = {
        'User': ['id (PK)', 'username', 'email', 'phone', 'first_name', 'last_name', 'gender', 'status'],
        'Role': ['id (PK)', 'role_type', 'name', 'description'],
        'Permission': ['id (PK)', 'name', 'permission_type', 'description'],
        'UserRole': ['id (PK)', 'user_id (FK)', 'role_id (FK)'],
        'RolePermission': ['id (PK)', 'role_id (FK)', 'permission_id (FK)'],
        'Continent': ['id (PK)', 'name', 'code', 'status'],
        'Country': ['id (PK)', 'name', 'code', 'continent_id (FK)', 'status'],
        'State': ['id (PK)', 'name', 'code', 'country_id (FK)', 'status'],
        'City': ['id (PK)', 'name', 'state_id (FK)', 'pin_code', 'status'],
        'ParkingLot': ['id (PK)', 'name', 'address', 'city_id (FK)', 'total_spots', 'available_spots', 'price_per_hour', 'status'],
        'ParkingSpot': ['id (PK)', 'spot_number', 'parking_lot_id (FK)', 'status'],
        'Reservation': ['id (PK)', 'user_id (FK)', 'parking_spot_id (FK)', 'start_time', 'end_time', 'vehicle_number', 'total_cost', 'status']
    }
    return attributes.get(entity_name, [])

if __name__ == "__main__":
    create_er_diagram()
    print("ER diagram saved as 'parking_management_er_diagram.pdf'") 