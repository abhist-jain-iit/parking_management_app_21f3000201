from app.models.enums import GeographyStatus
from app.extensions import db
from app.models.base import BaseModel

class Continent(BaseModel):
    __tablename__ = "continents"

    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)

    # Relationships
    countries = db.relationship('Country', back_populates='continent', cascade='all, delete', passive_deletes=True)
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "status": self.status.value,
            "countries_count": len([c for c in self.countries if not c.is_deleted])
        })
        return base_dict

    def __repr__(self):
        return f'<Continent {self.name}>'

class Country(BaseModel):
    __tablename__ = "countries"
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)  # ISO country code e.g., 'IN' for India
    continent_id = db.Column(db.Integer, db.ForeignKey('continents.id'), nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
    
    # Relationships
    continent = db.relationship('Continent', back_populates='countries')
    states = db.relationship('State', back_populates='country', cascade='all, delete', passive_deletes=True)
    
    __table_args__ = (db.UniqueConstraint('name', 'continent_id', name='unique_country_per_continent'),)
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "continent_name": self.continent.name if self.continent else None,
            "status": self.status.value,
            "states_count": len([s for s in self.states if not s.is_deleted])
        })
        return base_dict

    def __repr__(self):
        return f'<Country {self.name}>'

class State(BaseModel):
    __tablename__ = "states"
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)  # State code e.g., 'KA' for Karnataka
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
    
    # Relationships
    country = db.relationship('Country', back_populates='states')
    cities = db.relationship('City', back_populates='state', cascade='all, delete', passive_deletes=True)
    
    __table_args__ = (db.UniqueConstraint('name', 'country_id', name='unique_state_per_country'),)
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "country_name": self.country.name if self.country else None,
            "status": self.status.value,
            "cities_count": len([c for c in self.cities if not c.is_deleted])
        })
        return base_dict

    def __repr__(self):
        return f'<State {self.name}>'

class City(BaseModel):
    __tablename__ = "cities"
    
    name = db.Column(db.String(100), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    pin_code = db.Column(db.String(20), nullable=True)  # Optional pincode
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
    
    # Relationships
    state = db.relationship('State', back_populates='cities')
    # parking_lots will be added in next step
    
    __table_args__ = (db.UniqueConstraint('name', 'state_id', name='unique_city_per_state'),)
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "state_name": self.state.name if self.state else None,
            "country_name": self.state.country.name if self.state and self.state.country else None,
            "pin_code": self.pin_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status.value
        })
        return base_dict

    def __repr__(self):
        return f'<City {self.name}>'
