# 🚗 ParkEase - Vehicle Parking Management System

A comprehensive multi-user Flask web application for managing vehicle parking lots, spots, and reservations built for Modern Application Development I coursework.

## 📋 Project Overview

ParkEase is a smart parking management solution that allows users to find, reserve, and manage parking spots while providing administrators with complete control over parking facilities. The system supports 4-wheeler parking with real-time availability tracking.

## ✨ Features

### 👨‍💼 Admin Features
- **Complete System Control**: Full access to all system functionalities
- **User Management**: Create, edit, delete, and view all registered users
- **Parking Lot Management**: Create, edit, delete parking lots with customizable capacity and pricing
- **Parking Spot Management**: Automatic spot creation and manual management capabilities
- **Real-time Analytics**: Dashboard with revenue, occupancy, and usage statistics
- **Search & Filter**: Advanced search capabilities for users, lots, and spots

### 👤 User Features
- **Easy Registration/Login**: Secure user authentication with validation
- **Smart Parking Search**: Find available parking lots with filtering options
- **Quick Reservations**: Reserve parking spots with automatic assignment
- **Reservation Management**: View, modify, and cancel reservations
- **Real-time Updates**: Mark vehicle as parked and release spots
- **Personal Dashboard**: Track parking history and statistics

## 🛠️ Technical Stack

- **Backend**: Flask 3.1.1
- **Database**: SQLite (programmatically created)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-JWT-Extended with session management
- **Frontend**: Jinja2 templates, HTML5, CSS3, Bootstrap 5.1.3
- **Icons**: Font Awesome 6.0.0
- **Security**: Werkzeug password hashing

## 🏗️ Architecture

### Database Models
- **User Management**: Users, Roles, UserRoles, Permissions
- **Geography**: Continents, Countries, States, Cities
- **Parking System**: ParkingLots, ParkingSpots, Reservations

### Application Structure
```
Vehicle-Parking-App/
├── app/
│   ├── __init__.py           # App factory and configuration
│   ├── extensions.py         # Flask extensions
│   ├── decorators.py         # Custom decorators for permissions
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── base.py          # Base model class
│   │   ├── user.py          # User and role models
│   │   ├── parking.py       # Parking system models
│   │   ├── geography.py     # Location models
│   │   ├── permissions.py   # Permission models
│   │   ├── enums.py         # Enum definitions
│   │   └── database_setup.py # Database initialization
│   ├── routes/               # Application routes
│   │   ├── __init__.py
│   │   ├── main.py          # Home page routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin.py         # Admin management routes
│   │   └── user.py          # User functionality routes
│   ├── templates/            # Jinja2 templates
│   │   ├── home.html
│   │   ├── auth/            # Login/signup templates
│   │   ├── dashboards/      # Dashboard templates
│   │   ├── admin/           # Admin interface templates
│   │   └── user/            # User interface templates
│   ├── static/              # Static files (CSS, JS, images)
│   └── Data/
│       └── data.py          # Initial data for database
├── config.py                # Application configuration
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Vehicle-Parking-App
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python3 run.py
   ```

5. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000`

## 🔐 Default Login Credentials

### Administrator Access
- **Username**: `admin`
- **Password**: `Admin@123`
- **Capabilities**: Full system access

### User Registration
- New users can register through the signup page
- Email validation and strong password requirements enforced

## 📊 Database Schema

### Key Entities
1. **Users**: Store user information with role-based access
2. **ParkingLots**: Physical parking locations with pricing
3. **ParkingSpots**: Individual parking spaces within lots
4. **Reservations**: Booking records with time and cost tracking
5. **Geography**: Hierarchical location data (Continent → Country → State → City)

### Relationships
- Users can have multiple reservations
- ParkingLots contain multiple ParkingSpots
- Reservations link Users to specific ParkingSpots
- Role-based permissions control access levels

## 🎯 Core Functionality

### Parking Workflow
1. **User Registration**: Create account with personal details
2. **Browse Parking**: Search available parking lots by location/price
3. **Make Reservation**: Select duration and vehicle details
4. **Park Vehicle**: Mark reservation as occupied when arriving
5. **Release Spot**: Complete reservation when leaving

### Admin Workflow
1. **Dashboard Overview**: Monitor system statistics and activity
2. **Create Parking Lot**: Add new locations with capacity and pricing
3. **Manage Users**: View and administer user accounts
4. **Track Revenue**: Monitor financial performance
5. **System Analytics**: Access detailed reports and metrics

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern Interface**: Clean, intuitive design with gradient themes
- **Real-time Updates**: Dynamic cost calculation and status updates
- **Interactive Elements**: Hover effects, smooth transitions
- **Accessibility**: Proper semantic HTML and ARIA labels

## 🔒 Security Features

- **Password Security**: Bcrypt hashing with complexity requirements
- **Session Management**: Secure session handling with timeouts
- **Permission-based Access**: Role-based authorization system
- **Input Validation**: Server-side and client-side validation
- **CSRF Protection**: Form security tokens

## 🧪 Testing

The application includes several test scenarios:
- User registration and login
- Parking lot creation and management
- Reservation booking and management
- Admin dashboard functionality

## 📝 Assignment Requirements Compliance

✅ **Flask Backend**: Complete Flask application with blueprints
✅ **Jinja2 Templates**: All pages use template inheritance
✅ **Bootstrap Frontend**: Responsive design with Bootstrap 5
✅ **SQLite Database**: Programmatically created database
✅ **Multi-user Support**: Admin and regular user roles
✅ **CRUD Operations**: Full Create, Read, Update, Delete functionality
✅ **Business Logic**: Parking reservation and management system

## 🛣️ API Endpoints

### Authentication
- `GET/POST /auth/login` - User login
- `GET/POST /auth/signup` - User registration
- `POST /auth/logout` - User logout

### User Routes
- `GET /user/dashboard` - User dashboard
- `GET /user/parking-lots` - Browse parking lots
- `GET/POST /user/reserve/<lot_id>` - Make reservation
- `GET /user/reservations` - View user reservations
- `POST /user/reservations/<id>/park` - Mark as parked
- `POST /user/reservations/<id>/release` - Release spot

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - Manage users
- `GET /admin/parking` - Manage parking lots
- `GET/POST /admin/parking/lots/create` - Create new lot
- `GET/POST /admin/parking/lots/<id>/edit` - Edit parking lot

## 🔄 Future Enhancements

- **Payment Integration**: Online payment processing
- **Mobile App**: React Native mobile application
- **Real-time Notifications**: Push notifications for reservations
- **Advanced Analytics**: Machine learning insights
- **API Documentation**: Swagger/OpenAPI documentation
- **Multi-language Support**: Internationalization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is developed for educational purposes as part of Modern Application Development I coursework.

## 👨‍💻 Developer

**Project**: Vehicle Parking Management System  
**Course**: Modern Application Development I  
**Technologies**: Flask, SQLAlchemy, Bootstrap, SQLite  
**Year**: 2025

---

**Happy Parking! 🚗💨**