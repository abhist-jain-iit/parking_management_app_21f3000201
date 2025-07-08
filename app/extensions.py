from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# Here SQLAlchemy is ORM used to map with database.
db = SQLAlchemy()
login_manager = LoginManager()
