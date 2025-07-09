# Ease-Park! - Smart Parking Solutions

A comprehensive parking management application built with Flask, featuring user authentication, parking spot booking, and administrative management. Ease-Park! provides hassle-free parking solutions for both users and administrators.

## Features

### User Features
- **Dashboard**: View active, completed, and cancelled reservations
- **Booking**: Search and book parking spots by location
- **Profile Management**: Edit personal information
- **Reservation Management**: Vacate or cancel active reservations
- **Cost Tracking**: View total spending and current estimated bills

### Admin Features
- **Dashboard**: Overview of system statistics and revenue
- **User Management**: View, edit, and manage user accounts
- **Parking Management**: Manage parking lots and spots
- **Geography Management**: Manage continents, countries, states, and cities
- **Analytics**: View detailed reports and charts

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-JWT-Extended
- **Database**: SQLite
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **Authentication**: Session-based with JWT support

## Project Structure

```
parking_management_app/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── extensions.py            # Database and login manager
│   ├── decorators.py           # Permission decorators
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── database_setup.py   # Database initialization
│   │   ├── enums.py           # Enum definitions
│   │   ├── geography.py       # Geography models
│   │   ├── parking.py         # Parking models
│   │   ├── permissions.py     # Permission models
│   │   └── user.py           # User models
│   ├── routes/                # Route blueprints
│   │   ├── __init__.py
│   │   ├── admin.py          # Admin routes
│   │   ├── auth.py           # Authentication routes
│   │   ├── main.py           # Main routes
│   │   └── user.py           # User routes
│   ├── templates/            # HTML templates
│   │   ├── admin/           # Admin templates
│   │   ├── auth/            # Authentication templates
│   │   ├── dashboards/      # Dashboard templates
│   │   └── user/            # User templates
│   ├── static/              # Static files
│   │   └── js/             # JavaScript files
│   └── Data/               # Sample data
│       └── data.py         # Initial data
├── config.py               # Configuration settings
├── run.py                 # Application entry point
└── README.md             # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd parking_management_app
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-login flask-jwt-extended python-dotenv
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   - URL: http://localhost:5000
   - Admin login: admin / Admin@123

## Default Credentials

- **Admin**: username: `admin`, password: `Admin@123`
- **Sample Users**: Created automatically with the application

## Key Features

### Revenue Management
- **User Dashboard**: Shows total spent (completed reservations only) and total including cancelled
- **Admin Dashboard**: Shows total revenue including both completed and cancelled reservations
- **Billing Policy**: Users are charged for time used, even when cancelling (minimum 1 hour)

### Reservation System
- **Booking**: Users can book available spots with vehicle number
- **Vacate**: Complete reservations and calculate final cost
- **Cancel**: Cancel reservations with charge for time used
- **Status Tracking**: Active, Completed, and Cancelled statuses

### Permission System
- **Role-based**: Admin and User roles with specific permissions
- **Granular Control**: Individual permissions for different actions
- **Session Management**: Secure authentication with session and JWT support

## API Endpoints

### User Routes
- `GET /user/dashboard` - User dashboard
- `POST /user/book-spot/<spot_id>` - Book a parking spot
- `POST /user/vacate-reservation/<reservation_id>` - Vacate a spot
- `POST /user/cancel-reservation/<reservation_id>` - Cancel a reservation
- `GET /user/profile` - Edit profile
- `GET /user/book-reservation` - Booking page

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - Manage users
- `GET /admin/lots` - Manage parking lots
- `GET /admin/spots` - Manage parking spots
- `GET /admin/geography` - Manage geography data

### Authentication Routes
- `GET /auth/login` - Login page
- `POST /auth/login` - Login action
- `GET /auth/logout` - Logout
- `GET /auth/signup` - Registration page

## Database Schema

The application uses SQLAlchemy ORM with the following main models:

- **User**: User accounts with roles and permissions
- **ParkingLot**: Parking lots with location and pricing
- **ParkingSpot**: Individual parking spots within lots
- **Reservation**: User reservations with timing and cost
- **Geography**: Hierarchical location data (Continent → Country → State → City)

## Security Features

- **Password Hashing**: Secure password storage using werkzeug
- **Session Management**: Secure session handling
- **Permission System**: Role-based access control
- **Input Validation**: Form validation and sanitization
- **SQL Injection Protection**: Using SQLAlchemy ORM

## Production Considerations

- **Environment Variables**: Use `.env` file for sensitive configuration
- **Database**: Consider using PostgreSQL for production
- **Logging**: Implement proper logging for production
- **Security**: Enable HTTPS and secure headers
- **Performance**: Add caching and database optimization

## License

This project is licensed under the MIT License.
