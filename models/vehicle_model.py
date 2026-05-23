from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    vehicle_model = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    mileage = db.Column(db.Float, default=0)
    engine_temp = db.Column(db.Float, default=90)
    oil_quality = db.Column(db.Float, default=80)
    tire_pressure = db.Column(db.Float, default=32)
    brake_condition = db.Column(db.Float, default=80)
    battery_health = db.Column(db.Float, default=85)
    fuel_efficiency = db.Column(db.Float, default=30)
    service_history = db.Column(db.Integer, default=1)
    last_service_date = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    predictions = db.relationship('Prediction', backref='vehicle', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'vehicle_model': self.vehicle_model,
            'manufacturer': self.manufacturer,
            'mileage': self.mileage,
            'engine_temp': self.engine_temp,
            'oil_quality': self.oil_quality,
            'tire_pressure': self.tire_pressure,
            'brake_condition': self.brake_condition,
            'battery_health': self.battery_health,
            'fuel_efficiency': self.fuel_efficiency,
            'service_history': self.service_history,
            'last_service_date': self.last_service_date,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    health_score = db.Column(db.Float, nullable=False)
    maintenance_required = db.Column(db.Boolean, default=False)
    risk_level = db.Column(db.String(20), default='LOW')
    urgency = db.Column(db.String(20), default='ROUTINE')
    failure_components = db.Column(db.Text, default='[]')
    recommendations = db.Column(db.Text, default='[]')
    estimated_cost = db.Column(db.Float, default=0)
    accuracy = db.Column(db.Float, default=94.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'health_score': self.health_score,
            'maintenance_required': self.maintenance_required,
            'risk_level': self.risk_level,
            'urgency': self.urgency,
            'failure_components': json.loads(self.failure_components) if self.failure_components else [],
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'estimated_cost': self.estimated_cost,
            'accuracy': self.accuracy,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), default='INFO')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'message': self.message,
            'severity': self.severity,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
