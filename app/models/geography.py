from app.models.enums import GeographyStatus
from app.extensions import db
from app.models.base import BaseModel

class Continent(BaseModel):
    __tablename__ = "continents"

    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
    countries = db.relationship('Country', back_populates='continent', cascade='all, delete-orphan')
     
    def get_countries_count(self):
        return Country.query.filter_by(continent_id=self.id, status=GeographyStatus.ACTIVE).count()
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "status": self.status.value,
            "countries_count": self.get_countries_count()
        })
        return base_dict

    def __repr__(self):
        return f'<Continent {self.name}>'

class Country(BaseModel):
    __tablename__ = "countries"
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(3), nullable=False)
    continent_id = db.Column(db.Integer, db.ForeignKey('continents.id'), nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
    
    continent = db.relationship('Continent', back_populates='countries')
    states = db.relationship('State', back_populates='country', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('name', 'continent_id', name='unique_country_per_continent'),
        db.UniqueConstraint('code', name='unique_country_code')
    )
    
    def get_states_count(self):
        return State.query.filter_by(country_id=self.id, status=GeographyStatus.ACTIVE).count()
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "continent_name": self.continent.name if self.continent else None,
            "status": self.status.value,
            "states_count": self.get_states_count()
        })
        return base_dict

    def __repr__(self):
        return f'<Country {self.name}>'

class State(BaseModel):
    __tablename__ = "states"
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)
   
    country = db.relationship('Country', back_populates='states')
    cities = db.relationship('City', back_populates='state', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('name', 'country_id', name='unique_state_per_country'),
        db.UniqueConstraint('code', 'country_id', name='unique_state_code_per_country')
    )
    
    def get_cities_count(self):
        return City.query.filter_by(state_id=self.id, status=GeographyStatus.ACTIVE).count()
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "code": self.code,
            "country_name": self.country.name if self.country else None,
            "status": self.status.value,
            "cities_count": self.get_cities_count()
        })
        return base_dict

    def __repr__(self):
        return f'<State {self.name}>'

class City(BaseModel):
    __tablename__ = "cities"
    
    name = db.Column(db.String(100), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    pin_code = db.Column(db.String(20), nullable=True)
    status = db.Column(db.Enum(GeographyStatus), default=GeographyStatus.ACTIVE, nullable=False)   
    
    state = db.relationship('State', back_populates='cities')
    parking_lots = db.relationship('ParkingLot', back_populates='city', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('name', 'state_id', name='unique_city_per_state'),)
    
    def get_full_address(self):
        if self.state and self.state.country:
            return f"{self.name}, {self.state.name}, {self.state.country.name}"
        return self.name
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "state_name": self.state.name if self.state else None,
            "country_name": self.state.country.name if self.state and self.state.country else None,
            "pin_code": self.pin_code,
            "full_address": self.get_full_address(),
            "status": self.status.value
        })
        return base_dict

    def __repr__(self):
        return f'<City {self.name}>'