"""
Vehicle Maintenance Prediction System
Flask Application Entry Point
"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv

from config import Config
from models.vehicle_model import db, User, Vehicle, Prediction, Alert
from routes.auth import auth
from routes.api import api

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    CORS(app, supports_credentials=True)
    db.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(api)

    @app.route('/')
    def index():
        if not session.get('user_id'):
            return redirect(url_for('login_page'))
        return render_template('index.html', username=session.get('username', 'User'))

    @app.route('/login')
    def login_page():
        if session.get('user_id'):
            return redirect(url_for('index'))
        return render_template('login.html')

    with app.app_context():
        db.create_all()
        _seed_demo_data(app)

    return app


def _seed_demo_data(app):
    """Seed realistic demo vehicles for demonstration."""
    from werkzeug.security import generate_password_hash
    from models.ml_engine import ml_engine
    import json, random

    with app.app_context():
        if User.query.count() > 0:
            return

        # Create demo user
        demo_user = User(
            username='admin',
            email='admin@vmps.ai',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(demo_user)
        db.session.commit()

        # Demo vehicles
        demo_vehicles = [
            {
                'vehicle_number': 'MH-01-AB-1234',
                'vehicle_model': 'Model S',
                'manufacturer': 'Tesla',
                'mileage': 45000,
                'engine_temp': 88,
                'oil_quality': 82,
                'tire_pressure': 33,
                'brake_condition': 79,
                'battery_health': 91,
                'fuel_efficiency': 35,
                'service_history': 4,
                'last_service_date': '2024-11-15'
            },
            {
                'vehicle_number': 'DL-02-CD-5678',
                'vehicle_model': '5 Series',
                'manufacturer': 'BMW',
                'mileage': 110000,
                'engine_temp': 105,
                'oil_quality': 28,
                'tire_pressure': 28,
                'brake_condition': 35,
                'battery_health': 52,
                'fuel_efficiency': 18,
                'service_history': 8,
                'last_service_date': '2024-05-20'
            },
            {
                'vehicle_number': 'KA-03-EF-9012',
                'vehicle_model': 'F-150',
                'manufacturer': 'Ford',
                'mileage': 180000,
                'engine_temp': 118,
                'oil_quality': 12,
                'tire_pressure': 25,
                'brake_condition': 18,
                'battery_health': 21,
                'fuel_efficiency': 10,
                'service_history': 12,
                'last_service_date': '2023-09-01'
            },
            {
                'vehicle_number': 'TN-04-GH-3456',
                'vehicle_model': 'Civic',
                'manufacturer': 'Honda',
                'mileage': 62000,
                'engine_temp': 91,
                'oil_quality': 67,
                'tire_pressure': 31,
                'brake_condition': 68,
                'battery_health': 74,
                'fuel_efficiency': 28,
                'service_history': 6,
                'last_service_date': '2024-09-10'
            },
        ]

        for vdata in demo_vehicles:
            vehicle = Vehicle(user_id=demo_user.id, **vdata)
            db.session.add(vehicle)
            db.session.commit()

            result = ml_engine.predict(vdata)
            pred = Prediction(
                vehicle_id=vehicle.id,
                health_score=result['health_score'],
                maintenance_required=result['maintenance_required'],
                risk_level=result['risk_level'],
                urgency=result['urgency'],
                failure_components=json.dumps([result['failure_component']]),
                recommendations=json.dumps(result['recommendations']),
                estimated_cost=result['estimated_cost'],
                accuracy=result['accuracy']
            )
            db.session.add(pred)

            if result['urgency'] in ('CRITICAL', 'HIGH'):
                alert = Alert(
                    vehicle_id=vehicle.id,
                    message=f"Vehicle {vehicle.vehicle_number}: {result['failure_component']} — {result['urgency']}",
                    severity='CRITICAL' if result['urgency'] == 'CRITICAL' else 'WARNING'
                )
                db.session.add(alert)

        db.session.commit()
        print("[OK] Demo data seeded: 1 user, 4 vehicles, predictions and alerts created.")
        print("[INFO] Login: admin@vmps.ai / admin123")


if __name__ == '__main__':
    app = create_app()
    print("[VMPS] Vehicle Maintenance Prediction System starting...")
    print("[VMPS] Open browser at: http://localhost:5000")
    print("[VMPS] Demo login: admin@vmps.ai / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
